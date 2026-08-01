"""
ReAct (Reasoning + Acting) Agent 실행 엔진.
생각(Thought) -> 도구 선택 및 실행(Action & Observation) -> 최종 종합(Final Answer)의 자율 루프를 수행.
"""
import logging
import time
from typing import Dict, Any, List

from app.llm import get_agent_llm_provider
from app.tools import execute_tool

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agent")


class ReActAgentEngine:
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations

    def run(self, question: str, provider_name: str = "mock") -> Dict[str, Any]:
        """ReAct 자율 추론 루프 실행."""
        start_time = time.time()
        llm = get_agent_llm_provider(provider_name)
        
        trajectory: List[Dict[str, Any]] = []
        final_answer = ""
        iterations = 0

        log.info("=== Agent ReAct 루프 시작: 질문 '%s' ===", question)

        while iterations < self.max_iterations:
            iterations += 1
            log.info("--- ReAct Step %d ---", iterations)

            # LLM에게 다음 단계(Thought & Action 또는 Final Answer) 요청
            step_plan = llm.plan_next_step(question, trajectory)
            plan_type = step_plan.get("type")
            thought = step_plan.get("thought", "")

            if plan_type == "final_answer":
                final_answer = step_plan.get("answer", "")
                trajectory.append({
                    "step": iterations,
                    "thought": thought,
                    "action": "Final Answer",
                    "tool": None,
                    "observation": "최종 답변 완료",
                })
                log.info("Agent가 최종 답변을 완성했습니다.")
                break

            elif plan_type == "action":
                tool_name = step_plan.get("tool")
                kwargs = step_plan.get("kwargs", {})
                
                log.info("Agent 선택 도구: %s | 인자: %s", tool_name, kwargs)

                # 2. 도구 실제로 실행 (Observation 획득)
                observation = execute_tool(tool_name, **kwargs)
                log.info("도구 실행 결과(Observation): %s", observation[:100])

                trajectory.append({
                    "step": iterations,
                    "thought": thought,
                    "action": f"Call {tool_name}({kwargs})",
                    "tool": tool_name,
                    "kwargs": kwargs,
                    "observation": observation,
                })
            else:
                # 예외 타입 발생 시 멈춤
                final_answer = f"[Agent Error] 알 수 없는 단계 타입입니다: {plan_type}"
                break

        if iterations >= self.max_iterations and not final_answer:
            final_answer = f"[Agent Warning] 최대 도구 실행 횟수({self.max_iterations}회)를 초과하여 실행을 중단했습니다."

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "question": question,
            "final_answer": final_answer,
            "trajectory": trajectory,
            "total_steps": iterations,
            "latency_ms": latency_ms,
        }


# 전역 단일 에이전트 인스턴스
agent_engine = ReActAgentEngine()
