"""
AI Agent가 자율적으로 실행할 수 있는 외부 도구(Tools) 정의 모듈.
RAG 문서 검색, 사내 DB 조회, 이메일 알림 발송, 시스템 시간 조회를 포함함.
"""
import datetime
import logging

log = logging.getLogger("tools")


# --- 샘플 사내 DB ---
MOCK_EMPLOYEE_DB = {
    "김철수": {"emp_id": "E1001", "dept": "AI개발팀", "position": "책임연구원", "remaining_annual_leave": 8.5, "email": "chulsoo.kim@company.com"},
    "이영희": {"emp_id": "E1002", "dept": "IT기획팀", "position": "선임연구원", "remaining_annual_leave": 12.0, "email": "younghee.lee@company.com"},
    "박민수": {"emp_id": "E1003", "dept": "재무팀", "position": "수석연구원", "remaining_annual_leave": 3.0, "email": "minsoo.park@company.com"},
}


def search_policy_docs(query: str) -> str:
    """[Tool 1] 사내 규정 지식베이스(RAG) 검색 도구."""
    log.info("[Tool Exec] search_policy_docs call with query: %s", query)
    try:
        from app.rag_helper import search_docs
        results = search_docs(query)
        if not results:
            return "검색 결과: 관련 사내 규정 문서를 찾을 수 없습니다."
        return f"사내 규정 검색 결과:\n" + "\n---\n".join(results)
    except Exception as e:
        return f"사내 규정 검색 실패: {str(e)}"


def query_employee_db(employee_name: str) -> str:
    """[Tool 2] 사내 직원 정보 및 잔여 연차 조회 DB 도구."""
    log.info("[Tool Exec] query_employee_db call for: %s", employee_name)
    emp = MOCK_EMPLOYEE_DB.get(employee_name)
    if not emp:
        return f"DB 조회 결과: 직원 '{employee_name}'에 대한 정보를 찾을 수 없습니다. (등록된 직원: 김철수, 이영희, 박민수)"
    
    return (
        f"직원 DB 정보 [{employee_name}]:\n"
        f"- 사번: {emp['emp_id']}\n"
        f"- 부서: {emp['dept']}\n"
        f"- 직급: {emp['position']}\n"
        f"- 잔여 연차: {emp['remaining_annual_leave']}일\n"
        f"- 이메일: {emp['email']}"
    )


def send_notification_email(to_email: str, subject: str, body: str) -> str:
    """[Tool 3] 사내 이메일/알림 발송 도구."""
    log.info("[Tool Exec] send_notification_email to %s | subject: %s", to_email, subject)
    return (
        f"[발송 성공] 메일이 정상적으로 송신되었습니다.\n"
        f"- 수신자: {to_email}\n"
        f"- 제목: {subject}\n"
        f"- 내용 요약: {body[:60]}..."
    )


def get_current_time() -> str:
    """[Tool 4] 현재 시스템 날짜 및 시각 조회 도구."""
    log.info("[Tool Exec] get_current_time call")
    now = datetime.datetime.now()
    return f"현재 시각: {now.strftime('%Y년 %m월 %d일 %H시 %M분 %S초 (%A)')}"


# --- 도구 레지스트리 (Agent 사용 가이드 스키마) ---
AVAILABLE_TOOLS = {
    "search_policy_docs": {
        "func": search_policy_docs,
        "description": "사내 규정, 휴가 규칙, 경조금, 재택근무 등 사내 지식베이스 문서를 검색할 때 사용.",
        "parameters": {"query": "string (검색 키워드 또는 질문)"},
    },
    "query_employee_db": {
        "func": query_employee_db,
        "description": "특정 직원의 부서, 직급, 잔여 연차 일수, 이메일 주소를 조회할 때 사용.",
        "parameters": {"employee_name": "string (직원 성명, 예: 김철수, 이영희)"},
    },
    "send_notification_email": {
        "func": send_notification_email,
        "description": "직원에게 메일이나 알림을 송신할 때 사용.",
        "parameters": {
            "to_email": "string (수신자 이메일)",
            "subject": "string (메일 제목)",
            "body": "string (메일 본문)",
        },
    },
    "get_current_time": {
        "func": get_current_time,
        "description": "현재 날짜나 시각 정보가 필요한 경우 사용.",
        "parameters": {},
    },
}


def execute_tool(tool_name: str, **kwargs) -> str:
    """도구 이름과 전달인자로 실제 함수를 호출하는 래퍼."""
    if tool_name not in AVAILABLE_TOOLS:
        return f"[Tool Error] 존재하지 않는 도구 이름입니다: '{tool_name}'"
    tool_entry = AVAILABLE_TOOLS[tool_name]
    try:
        return tool_entry["func"](**kwargs)
    except Exception as e:
        return f"[Tool Exec Error] 도구 '{tool_name}' 실행 중 오류 발생: {str(e)}"
