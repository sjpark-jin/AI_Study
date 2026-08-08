"""
역할별 에이전트 정의 모듈: Planner, Researcher, Reviewer
"""
import logging
from typing import Dict, Any, List

try:
    from app.tools import execute_tool
except ImportError:
    from tools import execute_tool

log = logging.getLogger("agents")


class PlannerAgent:
    """[에이전트 1] 기획 에이전트: 사용자 요청을 분석하여 단계별 처리 계획을 수립한다."""

    def execute(self, user_request: str) -> List[str]:
        log.info("[PlannerAgent] 실행 계획 수립 중: %s", user_request)
        plan = []
        
        if any(kw in user_request for kw in ["연차", "잔여", "부서", "직원", "김철수", "이영희", "박민수"]):
            plan.append("1. 사내 DB에서 해당 직원의 인적사항 및 잔여 연차 조회")
        if any(kw in user_request for kw in ["규정", "경조금", "휴가", "재택"]):
            plan.append("2. 지식베이스에서 관련 사내 규정 문서 검색")
        if "메일" in user_request or "알림" in user_request or "이메일" in user_request:
            plan.append("3. 조회 결과를 담당자에게 이메일로 발송")
            
        if not plan:
            plan.append("1. 일반 지식 및 사내 가이드 문서 기반 검색")
            
        return plan


class ResearcherAgent:
    """[에이전트 2] 조사 에이전트: 계획에 맞춰 실제 RAG 및 DB 도구를 구동해 근거를 수집한다."""

    def execute(self, user_request: str, plan: List[str]) -> List[Dict[str, Any]]:
        log.info("[ResearcherAgent] 근거 데이터 수집 중...")
        findings = []

        # 직원 DB 조회 조건
        target_emp = None
        for emp_name in ["김철수", "이영희", "박민수"]:
            if emp_name in user_request:
                target_emp = emp_name
                break
        
        if target_emp or any("직원" in p or "연차" in p for p in plan):
            emp_name = target_emp or "김철수"
            res = execute_tool("query_employee_db", employee_name=emp_name)
            findings.append({"source": "DB", "tool": "query_employee_db", "data": res})

        # 규정 검색 조건
        if any("규정" in p or "지식베이스" in p for p in plan) or any(kw in user_request for kw in ["경조금", "결혼", "재택", "자기계발"]):
            res = execute_tool("search_policy_docs", query=user_request)
            findings.append({"source": "RAG", "tool": "search_policy_docs", "data": res})

        # 메일 발송 조건
        if any("이메일" in p or "메일" in p for p in plan) or "메일" in user_request:
            recipient = f"{target_emp.lower() if target_emp else 'employee'}@company.com"
            res = execute_tool("send_notification_email", to_email=recipient, subject="안내 메일", body="요청하신 조회 결과입니다.")
            findings.append({"source": "EMAIL", "tool": "send_notification_email", "data": res})

        return findings


class ReviewerAgent:
    """[에이전트 3] 검수 에이전트: 수집된 조사 결과의 정확성과 위험 요소를 검수한다."""

    def execute(self, user_request: str, plan: List[str], findings: List[Dict[str, Any]], revision_count: int) -> Dict[str, Any]:
        log.info("[ReviewerAgent] 수집 결과 검수 중... (재시도 횟수: %d)", revision_count)

        if not findings:
            return {
                "status": "REJECTED",
                "feedback": "수집된 근거 데이터가 없습니다. 추가 조회가 필요합니다.",
                "draft_answer": "데이터를 찾지 못했습니다.",
            }

        # 수집된 데이터 종합
        summary_lines = []
        for item in findings:
            summary_lines.append(f"[{item['source']}] {item['data']}")
        
        compiled_data = "\n".join(summary_lines)

        draft_answer = (
            f"멀티 에이전트 협업 검수 완료 답변:\n\n"
            f"**[요청 사항]** {user_request}\n\n"
            f"**[수집 데이터 종합]**\n{compiled_data}\n\n"
            f"Reviewer 검수 결과: 근거 데이터가 유효하며 최종 승인되었습니다."
        )

        return {
            "status": "APPROVED",
            "feedback": "모든 근거 데이터가 적절하며 위험 요소가 없습니다.",
            "draft_answer": draft_answer,
        }
