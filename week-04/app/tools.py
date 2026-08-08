"""
Week 4 멀티 에이전트용 실행 도구 정의.
"""
import datetime
import logging

log = logging.getLogger("tools")

MOCK_EMPLOYEE_DB = {
    "김철수": {"emp_id": "E1001", "dept": "AI개발팀", "position": "책임연구원", "remaining_annual_leave": 8.5, "email": "chulsoo.kim@company.com"},
    "이영희": {"emp_id": "E1002", "dept": "IT기획팀", "position": "선임연구원", "remaining_annual_leave": 12.0, "email": "younghee.lee@company.com"},
    "박민수": {"emp_id": "E1003", "dept": "재무팀", "position": "수석연구원", "remaining_annual_leave": 3.0, "email": "minsoo.park@company.com"},
}


def search_policy_docs(query: str) -> str:
    log.info("[Tool] search_policy_docs: %s", query)
    try:
        try:
            from app.rag_helper import search_docs
        except ImportError:
            from rag_helper import search_docs
        results = search_docs(query)
        if not results:
            return "사내 규정 문서에서 관련 검색 결과를 찾지 못했습니다."
        return "\n---\n".join(results)
    except Exception as e:
        return f"규정 검색 실패: {str(e)}"


def query_employee_db(employee_name: str) -> str:
    log.info("[Tool] query_employee_db: %s", employee_name)
    emp = MOCK_EMPLOYEE_DB.get(employee_name)
    if not emp:
        return f"직원 '{employee_name}' 정보 없음 (등록 직원: 김철수, 이영희, 박민수)"
    return (
        f"직원명: {employee_name} | 사번: {emp['emp_id']} | 부서: {emp['dept']} | "
        f"직급: {emp['position']} | 잔여연차: {emp['remaining_annual_leave']}일 | 메일: {emp['email']}"
    )


def send_notification_email(to_email: str, subject: str, body: str) -> str:
    log.info("[Tool] send_notification_email -> %s", to_email)
    return f"메일 발송 성공 (수신: {to_email}, 제목: {subject})"


def execute_tool(tool_name: str, **kwargs) -> str:
    if tool_name == "search_policy_docs":
        return search_policy_docs(kwargs.get("query", ""))
    elif tool_name == "query_employee_db":
        return query_employee_db(kwargs.get("employee_name", ""))
    elif tool_name == "send_notification_email":
        return send_notification_email(kwargs.get("to_email", ""), kwargs.get("subject", ""), kwargs.get("body", ""))
    return f"알 수 없는 도구: {tool_name}"
