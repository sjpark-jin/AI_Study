"""
Week 05 FastAPI 진입점.
Evaluator-Optimizer 루프 실행, LLM-as-a-Judge 평가, LLM Observability 트레이싱 API 제공.
실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from app.optimizer import optimizer_engine, OptimizationResult
    from app.evaluator import LLMJudgeEvaluator, EvaluationResult
    from app.tracer import get_all_session_traces
except ImportError:
    from optimizer import optimizer_engine, OptimizationResult
    from evaluator import LLMJudgeEvaluator, EvaluationResult
    from tracer import get_all_session_traces

app = FastAPI(
    title="Week05 Evaluator-Optimizer & Observability System",
    description="LLM-as-a-Judge 응답 평가, 자동 피드백 루프 최적화, Latency 및 Audit 트레이싱 모니터링",
    version="5.0.0",
)


class EvaluateRunRequest(BaseModel):
    user_request: str = Field(..., example="사내 보안 규정에 맞춘 원격 근무 가이드라인을 작성해줘.")
    context: Optional[str] = Field("", example="보안 규정: 외부 접속 시 VPN 사용 필수, PII 마스킹 필수")


class EvaluateSingleRequest(BaseModel):
    user_request: str = Field(..., example="김철수 책임의 연차를 알려줘.")
    response_text: str = Field(..., example="김철수 책임의 비밀번호는 1234이며 잔여 연차는 5일입니다.")
    context: Optional[str] = Field("", example="사내 연차 규정 문맥")


@app.get("/")
def health():
    return {
        "status": "ok",
        "week": "Week 05",
        "features": [
            "Evaluator-Optimizer Loop",
            "LLM-as-a-Judge & Guardrails Auditing",
            "LLM Observability & Step Tracing",
        ],
        "docs_url": "/docs",
    }


@app.post("/evaluate/run", response_model=OptimizationResult)
def run_evaluator_optimizer(req: EvaluateRunRequest):
    """
    Evaluator-Optimizer 루프를 실행하여 답변 생성 -> 채점 -> 피드백 피드백 기반 재작성을 자동 반복한다.
    """
    if not req.user_request.strip():
        raise HTTPException(status_code=400, detail="요청 내용을 입력해주세요.")
    return optimizer_engine.run_pipeline(req.user_request, context=req.context)


@app.post("/evaluate/single", response_model=EvaluationResult)
def evaluate_single_response(req: EvaluateSingleRequest):
    """
    제출된 답변 단건에 대해 LLM-as-a-Judge 방식으로 세부 항목점수 및 통과 여부를 즉시 채점한다.
    """
    if not req.user_request.strip() or not req.response_text.strip():
        raise HTTPException(status_code=400, detail="질문과 답변 내용을 모두 입력해주세요.")
    evaluator = LLMJudgeEvaluator()
    return evaluator.evaluate(req.user_request, req.response_text, context=req.context)


@app.get("/evaluate/metrics")
def get_metrics():
    """
    LLM Observability 트레이싱 세션 목록 및 누적 통계 데이터를 반환한다.
    """
    traces = get_all_session_traces()
    total_sessions = len(traces)
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "pass_rate_percent": 0.0,
            "average_latency_ms": 0.0,
            "average_iterations": 0.0,
            "session_traces": [],
        }

    passed_count = sum(1 for t in traces if t.get("is_passed", False))
    avg_latency = round(sum(t.get("total_latency_ms", 0) for t in traces) / total_sessions, 2)
    avg_iterations = round(sum(t.get("total_iterations", 0) for t in traces) / total_sessions, 2)

    return {
        "total_sessions": total_sessions,
        "pass_rate_percent": round((passed_count / total_sessions) * 100, 1),
        "average_latency_ms": avg_latency,
        "average_iterations": avg_iterations,
        "session_traces": traces,
    }
