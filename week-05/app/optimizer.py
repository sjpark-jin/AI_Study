"""
Week 05 Evaluator-Optimizer 반복 루프 모듈.
LLM 생성(Generator)과 채점(Evaluator)을 피드백 기반 루프로 연결하여 응답을 자동 개선하고,
전체 과정을 Observability 트레이스로 기록한다.
"""
import os
import time
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

try:
    from app.llm import get_llm_provider, BaseLLMProvider
    from app.evaluator import LLMJudgeEvaluator, EvaluationResult
    from app.tracer import ExecutionTracer, record_session_trace
except ImportError:
    from llm import get_llm_provider, BaseLLMProvider
    from evaluator import LLMJudgeEvaluator, EvaluationResult
    from tracer import ExecutionTracer, record_session_trace

log = logging.getLogger("optimizer")


class IterationLog(BaseModel):
    iteration: int
    candidate_response: str
    eval_result: EvaluationResult
    latency_ms: float


class OptimizationResult(BaseModel):
    user_request: str
    final_response: str
    is_passed: bool
    final_score: int
    total_iterations: int
    iteration_history: List[IterationLog]
    traces: List[Dict[str, Any]]
    total_latency_ms: float


class EvaluatorOptimizerEngine:
    def __init__(self, llm_provider: BaseLLMProvider = None):
        self.llm = llm_provider or get_llm_provider()
        self.evaluator = LLMJudgeEvaluator(llm_provider=self.llm)
        self.max_iterations = int(os.getenv("MAX_OPTIMIZE_ITERATIONS", "3"))

    def run_pipeline(self, user_request: str, context: str = "") -> OptimizationResult:
        tracer = ExecutionTracer()
        start_time = time.time()

        history: List[IterationLog] = []
        current_prompt = user_request
        current_response = ""
        is_passed = False
        final_score = 0

        for iter_num in range(1, self.max_iterations + 1):
            log.info("[Optimizer] 반복 %d/%d 실행 시작", iter_num, self.max_iterations)

            # 1. LLM 답변 생성 (Generator)
            gen_trace = tracer.start_trace(f"Iteration_{iter_num}_Generation", current_prompt)
            if iter_num == 1:
                system_prompt = "당신은 사내 전문 AI 보조입니다. 사용자의 질문에 명확하고 사실적으로 답변하세요."
                current_response = self.llm.generate(current_prompt, system_prompt=system_prompt)
            else:
                system_prompt = (
                    "당신은 평가관의 피드백을 반영해 응답을 고도화하는 전문 AI입니다.\n"
                    "이전 답변의 부족한 점을 보완하고 질문 조건과 안전성 기준을 완벽히 만족하도록 재작성하세요."
                )
                current_response = self.llm.generate(current_prompt, system_prompt=system_prompt)
            gen_trace.complete(current_response, metadata={"iteration": iter_num})

            # 2. LLM-as-a-Judge 채점 (Evaluator)
            eval_trace = tracer.start_trace(f"Iteration_{iter_num}_Evaluation", current_response)
            eval_res = self.evaluator.evaluate(user_request, current_response, context=context)
            eval_trace.complete(eval_res.model_dump(), metadata={"score": eval_res.overall_score, "passed": eval_res.is_passed})

            # 히스토리 기록
            iter_latency = gen_trace.latency_ms + eval_trace.latency_ms
            history.append(
                IterationLog(
                    iteration=iter_num,
                    candidate_response=current_response,
                    eval_result=eval_res,
                    latency_ms=iter_latency,
                )
            )

            final_score = eval_res.overall_score
            if eval_res.is_passed:
                is_passed = True
                log.info("[Optimizer] 반복 %d회차 만에 기준 점수 통과 (%d점)", iter_num, final_score)
                break

            # 통과 실패 시 피드백 기반 개선 프롬프트 재구성
            log.info("[Optimizer] 통과 실패 (%d점). 피드백 반영 프롬프트 재구성", final_score)
            current_prompt = (
                f"[원래 사용자 질문]\n{user_request}\n\n"
                f"[이전 생성 답변]\n{current_response}\n\n"
                f"[평가관 피드백 및 개선 요구사항]\n{eval_res.feedback}\n"
                f"[감지된 문제점]: {', '.join(eval_res.detected_issues) if eval_res.detected_issues else '없음'}\n\n"
                f"위 피드백을 완벽히 반영하여 수정된 최선의 답변을 작성해주세요."
            )

        total_latency = round((time.time() - start_time) * 1000, 2)
        traces_list = tracer.export_all()

        session_record = {
            "session_id": tracer.session_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_request": user_request,
            "final_score": final_score,
            "is_passed": is_passed,
            "total_iterations": len(history),
            "total_latency_ms": total_latency,
            "traces": traces_list,
        }
        record_session_trace(session_record)

        return OptimizationResult(
            user_request=user_request,
            final_response=current_response,
            is_passed=is_passed,
            final_score=final_score,
            total_iterations=len(history),
            iteration_history=history,
            traces=traces_list,
            total_latency_ms=total_latency,
        )


optimizer_engine = EvaluatorOptimizerEngine()
