"""
Week 5 LLM Provider 모듈.
.env 환경변수를 자동 로드하며, Mock 및 OpenAI API 연동 지원.
"""
import logging
import os
from abc import ABC, abstractmethod

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("llm")


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        pass


class MockLLMProvider(BaseLLMProvider):
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        log.info("[MockLLM] 응답 생성 완료")
        if "피드백" in prompt or "개선" in prompt or "수정" in prompt:
            return (
                "상세 보완 응답:\n"
                "1. 질문 의도: 요구사항의 모든 상세 조건을 충족하는 정교한 답변 작성.\n"
                "2. 근거 및 내용: 객관적 사실에 기반하며 환각(Hallucination) 없이 정확한 수치와 절차 명시.\n"
                "3. 보안 및 준수: 보안 규정을 준수하며 안전성 검증을 통과한 답변입니다."
            )
        return (
            f"[초안 응답] 요청하신 '{prompt}'에 대한 기본 답변입니다. "
            "상세 조건과 검증 근거를 포함하여 정확하게 안내해 드립니다."
        )


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return "[Error] OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 키를 추가해주세요."
        try:
            import requests
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "temperature": 0.3},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error("OpenAI API 호출 실패: %s", e)
            return f"[LLM Error] OpenAI 연동 실패: {str(e)}"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    if not provider_name:
        provider_name = os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    if provider_name.lower() == "openai":
        return OpenAIProvider()
    return MockLLMProvider()
