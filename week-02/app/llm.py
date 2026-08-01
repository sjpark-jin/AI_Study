"""
LLM Provider 추상화 모듈.
.env 환경변수를 자동 로드하며, API 키 없이도 즉시 테스트 가능한 Mock LLM Provider 기본 제공.
필요 시 OpenAI / Ollama / Custom API로 용이하게 확장 가능한 구조.
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()  # .env 파일에서 환경변수 자동 로드
except ImportError:
    pass

log = logging.getLogger("llm")


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, history: List[Dict[str, str]], question: str, context: str) -> str:
        """LLM 답변 생성 메서드 인터페이스."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """API 키 없이 컨텍스트를 기반으로 자연스러운 한국어 답변을 가상 생성하는 Mock LLM."""
    
    def generate(self, system_prompt: str, history: List[Dict[str, str]], question: str, context: str) -> str:
        log.info("[MockLLM] 답변 생성 중...")
        
        # 근거 컨텍스트가 전혀 없는 경우 (환각 방지 처리 확인)
        if not context or "관련 근거 문서를 찾지 못했습니다" in context:
            return "죄송합니다. 제공해주신 사내 규정 문서에서는 해당 질문에 대한 근거를 찾을 수 없습니다. (환각 방지: 없는 정보는 답변하지 않습니다.)"
        
        # 이전 대화 맥락 요약 생성 (히스토리가 있는 경우)
        history_summary = ""
        if history:
            last_q = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
            if last_q:
                history_summary = f"(이전 대화 '{last_q}' 맥락 참조) "

        # 컨텍스트 기반 키워드 조합하여 자연스러운 답변 출력
        lines = [line.strip() for line in context.split("\n") if line.strip() and not line.startswith("---")]
        key_sentences = "\n• ".join(lines[:3])
        
        answer = (
            f"안녕하세요! 사내 규정 문서를 바탕으로 질문에 대해 {history_summary}답변드립니다.\n\n"
            f"**관련 규정 요약:**\n• {key_sentences}\n\n"
            f"추가 문의사항이 있으시면 언제든지 편하게 질문해주세요!"
        )
        return answer


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API 연동 Provider (OPENAI_API_KEY 필요)."""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate(self, system_prompt: str, history: List[Dict[str, str]], question: str, context: str) -> str:
        if not self.api_key:
            return "[Error] OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 기입하거나 Mock Provider를 사용해주세요."
        try:
            import requests
            messages = [{"role": "system", "content": f"{system_prompt}\n\n[참조 컨텍스트]:\n{context}"}]
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})

            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "temperature": 0.2},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error("OpenAI API 호출 실패: %s", e)
            return f"[LLM Error] OpenAI 연동 실패: {str(e)}"


def get_llm_provider(provider_type: str = None) -> BaseLLMProvider:
    """.env 설정 또는 전달받은 파라미터에 따라 적절한 LLM Provider 객체 반환."""
    if not provider_type:
        provider_type = os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    provider_type = provider_type.lower()
    if provider_type == "openai":
        return OpenAIProvider()
    return MockLLMProvider()
