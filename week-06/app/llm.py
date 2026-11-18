"""
Week 06 LLM Provider 모듈.
.env 환경변수를 지원하며, Mock 및 OpenAI API 연동을 제공합니다.
실제 API 키가 없어도 모든 RAG 검색, 답변 생성 및 Ragas 평가 시뮬레이션이 즉시 동작합니다.
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
        """프롬프트와 시스템 프롬프트를 받아 답변을 생성한다."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    API 키 없이도 로컬에서 신속한 테스트와 학습이 가능하도록 설계된 고도화 Mock LLM.
    전달된 검색 문맥(Context)을 파싱하여 실제 RAG 답변 형식으로 충실하게 응답합니다.
    """
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        log.info("[MockLLM] 질의 처리 시작")

        # 1. Ragas 평가용 프롬프트인지 감지 (Faithfulness, Relevance, Context Precision)
        if "Faithfulness" in prompt or "충실도" in prompt:
            return '{"score": 95, "verdict": "PASS", "reason": "생성된 답변의 모든 문장이 제공된 Context 내 사실에 완벽히 부합합니다."}'
        if "Relevance" in prompt or "관련성" in prompt:
            return '{"score": 90, "verdict": "PASS", "reason": "사용자의 질문 핵심 의도에 초점을 맞춰 누락 없이 답변을 제공했습니다."}'
        if "Context Precision" in prompt or "정확도" in prompt:
            return '{"score": 88, "verdict": "PASS", "reason": "질문 해결에 필요한 핵심 기술 문서가 검색 상위 랭킹(1, 2순위)에 정확히 배치되었습니다."}'

        # 2. 일반 RAG 질의 생성 응답
        if "K8S-INGRESS-404" in prompt:
            return (
                "사내 Kubernetes 인그레스 장애(에러 코드: K8S-INGRESS-404)에 대한 조치 방안입니다:\n"
                "1. 원인: 클러스터 외부 인입 트래픽이 차단되거나 백엔드 서비스 파드(Pod)로 라우팅되지 못할 때 발생합니다.\n"
                "2. 조치 절차: `kubectl describe ingress -n production` 명령어로 Annotations 설정 및 백엔드 포트 포워딩 상태를 점검하십시오.\n"
                "3. 로그 확인: `/var/log/nginx-ingress/access.log` 경로에서 추가 에러 로그를 점검하시기 바랍니다."
            )
        elif "AUTH-JWT-V2" in prompt or "인증" in prompt:
            return (
                "AUTH-JWT-V2 통합 인증 규격 안내입니다:\n"
                "1. 유효 시간: Access Token은 15분, Refresh Token은 7일간 유효합니다.\n"
                "2. 암호화: RSA 4096-bit 비대칭 키 페어 기반 RS256 서명 알고리즘을 사용합니다.\n"
                "3. 헤더 규칙: 외부 게이트웨이 요청 시 `X-Enterprise-Auth-Token` 헤더에 권한 위임 플래그와 함께 전달되어야 합니다."
            )
        elif "DB-CONN-TIMEOUT-1002" in prompt or "커넥션" in prompt:
            return (
                "데이터베이스 커넥션 타임아웃(DB-CONN-TIMEOUT-1002) 조치 가이드입니다:\n"
                "1. 원인: 급격한 트래픽 증가나 장기 실행 슬로우 쿼리로 인한 HikariCP 풀 고갈 현상입니다.\n"
                "2. 권장 설정: maximumPoolSize=30, connectionTimeout=3000ms를 유지하십시오.\n"
                "3. 대응: 슬로우 쿼리 로그를 수집하여 인덱스 누락 및 N+1 쿼리 여부를 프로파일링해야 합니다."
            )
        elif "원격 근무" in prompt or "VPN" in prompt:
            return (
                "사내 원격 근무 및 보안 접속 지침입니다:\n"
                "1. 네트워크: 반드시 사내 공인 VPN(Cisco AnyConnect / WireGuard)을 경유해야 합니다.\n"
                "2. 보안 금지사항: 개인 로컬 디스크에 소스코드나 DB 덤프를 직접 보관하는 것은 제14조에 의해 엄격히 금지됩니다.\n"
                "3. 인증 절차: OTP/FIDO2 2단계 인증을 거쳐야 하며, 3회 실패 시 계정이 자동 잠금됩니다."
            )

        # 기본 응답
        return (
            f"검색된 사내 문서 문맥을 바탕으로 안내해 드립니다.\n"
            f"질문하신 내용에 대해 제공된 지식베이스 문맥을 충실히 반영하여 사실 기반으로 정리하였습니다.\n"
            f"(질의 키워드 분석 완료: 문맥 내 핵심 기술 사양 및 절차를 준수하여 답변을 구성함)"
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
                json={"model": self.model, "messages": messages, "temperature": 0.2},
                timeout=25,
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
