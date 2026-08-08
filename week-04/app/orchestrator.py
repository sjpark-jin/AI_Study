"""
멀티 에이전트 오케스트레이터: 상태 머신(State Flow) 기반의 에이전트 간 제어 흐름을 관리한다.
"""
import logging
import time
from typing import Dict, Any, List

try:
    from app.agents import PlannerAgent, ResearcherAgent, ReviewerAgent
except ImportError:
    from agents import PlannerAgent, ResearcherAgent, ReviewerAgent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("orchestrator")


class MultiAgentOrchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.reviewer = ReviewerAgent()
        self.max_revisions = 2

    def run_workflow(self, user_request: str) -> Dict[str, Any]:
        start_time = time.time()
        
        # 상태(State) 객체 초기화
        state: Dict[str, Any] = {
            "user_request": user_request,
            "current_step": "PLAN",
            "plan": [],
            "research_findings": [],
            "review_result": {},
            "history_logs": [],
            "revision_count": 0,
        }

        log.info("=== Multi-Agent 워크플로 시작: %s ===", user_request)

        while state["current_step"] != "FINISH":
            current = state["current_step"]

            if current == "PLAN":
                log.info("[State Transition] -> PLAN")
                state["plan"] = self.planner.execute(user_request)
                state["history_logs"].append({
                    "node": "PLAN",
                    "action": "수립된 실행 계획",
                    "output": state["plan"],
                })
                state["current_step"] = "RESEARCH"

            elif current == "RESEARCH":
                log.info("[State Transition] -> RESEARCH")
                state["research_findings"] = self.researcher.execute(user_request, state["plan"])
                state["history_logs"].append({
                    "node": "RESEARCH",
                    "action": "근거 수집 완료",
                    "output": state["research_findings"],
                })
                state["current_step"] = "REVIEW"

            elif current == "REVIEW":
                log.info("[State Transition] -> REVIEW")
                review_res = self.reviewer.execute(
                    user_request=user_request,
                    plan=state["plan"],
                    findings=state["research_findings"],
                    revision_count=state["revision_count"],
                )
                state["review_result"] = review_res
                state["history_logs"].append({
                    "node": "REVIEW",
                    "action": f"검수 결과: {review_res['status']}",
                    "output": review_res,
                })

                if review_res["status"] == "APPROVED":
                    state["current_step"] = "FINISH"
                else:
                    state["revision_count"] += 1
                    if state["revision_count"] >= self.max_revisions:
                        log.warning("최대 재시도 횟수 초과로 강제 종료")
                        state["current_step"] = "FINISH"
                    else:
                        log.info("검수 실패로 조회를 재시도합니다.")
                        state["current_step"] = "RESEARCH"

        latency_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "user_request": user_request,
            "final_answer": state["review_result"].get("draft_answer", "답변 생성 실패"),
            "status": state["review_result"].get("status", "UNKNOWN"),
            "plan": state["plan"],
            "findings_count": len(state["research_findings"]),
            "workflow_history": state["history_logs"],
            "total_revisions": state["revision_count"],
            "latency_ms": latency_ms,
        }


orchestrator = MultiAgentOrchestrator()
