"""
Week 3 Agent LLM Provider 모듈.
.env 환경변수를 자동 로드하며, API 키 없이 ReAct (Reasoning + Acting) 도구 호출 추적 과정을 시뮬레이션하는 Mock Agent LLM 제공.
"""
import logging
import os
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("agent_llm")


class BaseAgentLLMProvider(ABC):
    @abstractmethod
    def plan_next_step(self, question: str, trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ReAct 추론 루프의 다음 단계를 결정.
        반환 형식:
        - Tool 호출 필요 시: {"type": "action", "thought": "...", "tool": "도구명", "kwargs": {...}}
        - 최종 답변 완성 시: {"type": "final_answer", "thought": "...", "answer": "..."}
        """
        pass


class MockAgentLLMProvider(BaseAgentLLMProvider):
    """ReAct Agent 추론 및 도구 호출 과정을 시뮬레이션하는 Smart Mock Agent LLM."""

    def plan_next_step(self, question: str, trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        log.info("[MockAgentLLM] ReAct 단계 계산 중... (현재 Step 수: %d)", len(trajectory))
        
        # 이전 실행 이력(Observation) 분석
        has_query_db = any(step.get("tool") == "query_employee_db" for step in trajectory)
        has_search_policy = any(step.get("tool") == "search_policy_docs" for step in trajectory)
        has_send_email = any(step.get("tool") == "send_notification_email" for step in trajectory)
        has_get_time = any(step.get("tool") == "get_current_time" for step in trajectory)

        # 1. 질문 분기 판단
        # A. 직원 DB 조회 및 연차 질문
        if any(keyword in question for keyword in ["연차", "잔여", "부서", "직급", "김철수", "이영희", "박민수", "직원"]):
            target_name = "김철수"
            if "이영희" in question:
                target_name = "이영희"
            elif "박민수" in question:
                target_name = "박민수"

            if not has_query_db:
                return {
                    "type": "action",
                    "thought": f"사용자가 {target_name} 직원의 정보 및 연차 일수를 물었습니다. 사내 직원 DB 조회 도구(query_employee_db)를 호출합니다.",
                    "tool": "query_employee_db",
                    "kwargs": {"employee_name": target_name},
                }
            
            # 메일 발송도 함께 요청된 경우
            if ("메일" in question or "이메일" in question or "알림" in question) and not has_send_email:
                db_obs = next((step["observation"] for step in trajectory if step.get("tool") == "query_employee_db"), "")
                return {
                    "type": "action",
                    "thought": f"직원 DB 조회가 완료되었습니다. 사용자 요청에 따라 해당 직원에게 알림 메일 발송 도구(send_notification_email)를 실행합니다.",
                    "tool": "send_notification_email",
                    "kwargs": {
                        "to_email": f"{target_name.lower()}@company.com",
                        "subject": "연차 잔여일수 및 사내 안내",
                        "body": f"안녕하세요 {target_name}님, 문의하신 DB 조회 결과 안내드립니다.",
                    },
                }

            # 모든 필요 도구 실행 완료 -> 최종 답변
            db_obs = next((step["observation"] for step in trajectory if step.get("tool") == "query_employee_db"), "정보 없음")
            email_obs = next((step["observation"] for step in trajectory if step.get("tool") == "send_notification_email"), "")
            
            answer_text = (
                f"ReAct Agent가 사내 DB를 성공적으로 조회하여 답변드립니다.\n\n"
                f"**[조회 결과]**\n{db_obs}"
            )
            if email_obs:
                answer_text += f"\n\n**[메일 발송 안내]**\n{email_obs}"

            return {
                "type": "final_answer",
                "thought": "모든 도구 실행 결과(Observation)를 종합하여 최종 사용자 답변을 작성합니다.",
                "answer": answer_text,
            }

        # B. 사내 규정 / 경조금 / 휴가 정책 질문
        elif any(keyword in question for keyword in ["규정", "결혼", "사망", "경조금", "재택", "자기계발", "도서"]):
            if not has_search_policy:
                return {
                    "type": "action",
                    "thought": "사내 규정과 관련된 질의입니다. 지식베이스 RAG 검색 도구(search_policy_docs)를 호출합니다.",
                    "tool": "search_policy_docs",
                    "kwargs": {"query": question},
                }
            
            policy_obs = next((step["observation"] for step in trajectory if step.get("tool") == "search_policy_docs"), "")
            return {
                "type": "final_answer",
                "thought": "사내 규정 문서 검색 결과를 확인했으므로 답변을 종합합니다.",
                "answer": f"사내 규정 지식베이스 검색 결과를 바탕으로 답변드립니다:\n\n{policy_obs}",
            }

        # C. 시간/날짜 질문
        elif any(keyword in question for keyword in ["시간", "시각", "오늘", "날짜", "며칠"]):
            if not has_get_time:
                return {
                    "type": "action",
                    "thought": "현재 시간 조회가 필요합니다. get_current_time 도구를 호출합니다.",
                    "tool": "get_current_time",
                    "kwargs": {},
                }
            
            time_obs = next((step["observation"] for step in trajectory if step.get("tool") == "get_current_time"), "")
            return {
                "type": "final_answer",
                "thought": "시간 조회가 완료되었습니다.",
                "answer": f"Agent 확인 결과: {time_obs}",
            }

        # D. 일반 질문 / 기본 처리
        else:
            return {
                "type": "final_answer",
                "thought": "별도의 외부 도구가 필요하지 않은 질문입니다.",
                "answer": f"안녕하세요! AI Agent입니다. 질문해주신 '{question}'에 대해 도구를 구동하지 않고 직접 답변드립니다. 사내 연차/규정/시간/메일 발송 등은 도구를 활용해 답변할 수 있습니다.",
            }


class OpenAIAgentProvider(BaseAgentLLMProvider):
    """OpenAI API 연동 Agent Provider (OPENAI_API_KEY 필요)."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def plan_next_step(self, question: str, trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.api_key:
            return {
                "type": "final_answer",
                "thought": "OPENAI_API_KEY가 존재하지 않습니다.",
                "answer": "[Error] OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 키를 기입하거나 Mock Provider를 선택해주세요.",
            }
        # OpenAI API Key가 기재된 경우 실제 GPT Function Calling 요청을 연동
        # 본 실습 환경에서는 가이드 제공
        mock = MockAgentLLMProvider()
        return mock.plan_next_step(question, trajectory)


def get_agent_llm_provider(provider_type: str = None) -> BaseAgentLLMProvider:
    if not provider_type:
        provider_type = os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    if provider_type.lower() == "openai":
        return OpenAIAgentProvider()
    return MockAgentLLMProvider()
