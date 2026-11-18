"""
Week 07 — System Two (생성형 LLM) Provider 모듈.
TypeSafe AI Jev(System One)가 확률적 의사결정 및 라우팅/가드레일 게이트키핑을 완료한 후,
실제 고객/엔지니어에게 전달할 자연어 액션 리포트나 안내문을 합성할 때 연동됩니다.
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
    """
    외부 API 키 없이도 System 1 (Jev) + System 2 (Generative LLM) 하이브리드 파이프라인을
    완벽하게 체험할 수 있는 로컬 Mock 프로바이더.
    """
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        log.info("[MockLLM] System 2 자연어 응답 합성 시작")

        if "SECURITY_LOCKDOWN" in prompt or "보안" in prompt and ("해외 IP" in prompt or "ignore previous" in prompt.lower()):
            return (
                "[보안 관제 자동 차단 리포트]\n"
                "1. 판정 결과: Jev System One 엔진에서 보안 위협 확률(Noul)이 임계치를 초과하여 즉시 격리 조치되었습니다.\n"
                "2. 자동 실행 액션: 해당 계정의 API 토큰을 일시 무효화하고 비정상 IP(185.220.101.44)를 WAF 차단 목록에 등록했습니다.\n"
                "3. 후속 절차: 사내 CERT 보안팀 전용 큐로 패킷 덤프가 이관되었으며System Two LLM 프롬프트 실행은 안전하게 차단되었습니다."
            )
        elif "AUTO_REFUND_PIPELINE" in prompt or ("환불" in prompt and "중복" in prompt):
            return (
                "[결제/환불 자동 처리 안내]\n"
                "1. 판정 결과: 담당 부서 'Billing' 분류 신뢰도(Confidence) 및 환불 요청 확률(Noul)이 자동 승인 기준을 충족했습니다.\n"
                "2. 자동 실행 액션: Stripe/PG 결제 게이트웨이 API를 호출하여 중복 승인된 $1,200 트랜잭션(ORD-7741) 자동 환불을 실행했습니다.\n"
                "3. 고객 안내: 영업일 기준 2~3일 내 카드사 전표 취소가 완료되며 영수증이 이메일로 자동 발송됩니다."
            )
        elif "SRE_PAGER_ESCALATION" in prompt or "504" in prompt or "장애" in prompt:
            return (
                "[SRE 긴급 장애 대응 런북 가동 리포트]\n"
                "1. 판정 결과: Jev Score 프리미티브 평가 결과 장애 심각도(Severity Score)가 최고 위험 구간으로 측정되었습니다.\n"
                "2. 자동 실행 액션: PagerDuty P1 알람을 발송하고 `order-payment-api` 클러스터의 Read Replica 오토스케일링을 트리거했습니다.\n"
                "3. 엔지니어 가이드: HikariCP 커넥션 풀 점유 현황을 확인하고 최근 배포된 릴리즈 롤백 여부를 승인해 주십시오."
            )
        elif "HITL_HUMAN_QUEUE" in prompt:
            return (
                "[Human-in-the-Loop 수동 검토 이관 리포트]\n"
                "1. 판정 결과: 단일 의도가 아닌 복합 문의(요금제 + API 기술 스펙 + 보안 감사 서류)로 감지되어 Choice 신뢰도(Confidence)가 자동화 임계값 미만입니다.\n"
                "2. 안전 제어: 잘못된 부서로 오배정하거나 부정확한 자동 답변을 보내는 대신, Jev가 산출한 부서별 확률 분포표를 첨부하여 시니어 매니저 대시보드로 에스컬레이션했습니다."
            )

        return (
            "[System 1 + System 2 하이브리드 처리 완료]\n"
            "TypeSafe AI Jev의 강타입 확률 평가 결과를 바탕으로 안전성이 검증된 상태에 한해 맞춤형 응답을 생성했습니다."
        )


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return MockLLMProvider().generate(prompt, system_prompt)
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
            return MockLLMProvider().generate(prompt, system_prompt)


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    if not provider_name:
        provider_name = os.getenv("DEFAULT_LLM_PROVIDER", "mock")
    if provider_name.lower() == "openai":
        return OpenAIProvider()
    return MockLLMProvider()

