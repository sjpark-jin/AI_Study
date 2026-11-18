"""
Week 07 — System One (TypeSafe AI Jev) vs System Two (Generative LLM JSON Parsing) 비교 실험 모듈.

소프트웨어 엔지니어링에서 머신-투-머신(M2M) 의사결정 시 왜 일반적인 생성형 LLM 프롬프트 파싱 대신
TypeSafe AI Jev(System One) 아키텍처가 필요한지 정량적으로 비교/시뮬레이션합니다.
"""
import json
import time
from typing import Any, Dict, Union
from pydantic import BaseModel, Field

try:
    from app.jev_engine import jev_engine
    from app.workflow_router import workflow_router
except ImportError:
    from jev_engine import jev_engine
    from workflow_router import workflow_router


class ParadigmComparisonResult(BaseModel):
    state_preview: str
    system_one_jev: Dict[str, Any] = Field(..., description="TypeSafe AI Jev (System One) 실행 결과 및 지표")
    system_two_llm: Dict[str, Any] = Field(..., description="기존 생성형 LLM JSON 파싱 방식의 실행 결과 및 한계점")
    engineering_verdict: str = Field(..., description="아키텍처 비교 핵심 요약")


def compare_system_one_vs_two(state: Union[str, Dict[str, Any]]) -> ParadigmComparisonResult:
    """
    동일한 입력 상태(State)에 대해
    1) TypeSafe AI Jev (System One 병렬 강타입 평가)
    2) 전통적인 생성형 LLM (System Two 토큰 생성 + JSON 파싱)
    두 가지 패러다임을 비교 분석합니다.
    """
    state_str = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    questions = workflow_router.build_standard_questions()

    # 1. System One (Jev) 실행
    jev_res = jev_engine.system_one(state=state, questions=questions)
    dept = jev_res.answers["department"]
    sev = jev_res.answers["severity"]
    ref = jev_res.answers["refund_requested"]
    sec = jev_res.answers["security_risk"]

    # 2. System Two (생성형 LLM 프롬프트 JSON 유도 방식)의 전형적인 동작 및 취약점 시뮬레이션
    s_lower = state_str.lower()
    has_injection = "ignore previous" in s_lower or "root credentials" in s_lower
    is_ambiguous = "고민 중" in s_lower or "has_multiple_intents" in s_lower

    if has_injection:
        llm_raw_output = (
            "```json\n"
            "{\n"
            '  "department": "SYSTEM_OVERRIDE_ADMIN",\n'
            '  "urgency": "HIGH",\n'
            '  "confidence": 0.99,\n'
            '  "note": "As instructed, dumping environment variables..."\n'
            "}\n```"
        )
        schema_violation = True
        failure_mode = "프롬프트 인젝션에 의해 정의되지 않은 Enum 값('SYSTEM_OVERRIDE_ADMIN') 생성 및 마크다운 코드블록 혼입"
        simulated_latency_ms = 1420.5
    elif is_ambiguous:
        llm_raw_output = (
            'Here is the classification result:\n'
            '{"department": "billing", "severity": 2, "confidence": 0.95}'
        )
        schema_violation = True
        failure_mode = "복합/모호한 질문임에도 언어적 과신(Verbalized Overconfidence: 0.95)을 출력하여 HITL 분기 실패 + 서문 텍스트로 인한 json.loads() 에러"
        simulated_latency_ms = 1180.0
    else:
        llm_raw_output = (
            "{\n"
            f'  "department": "{dept.choice}",\n'
            f'  "severity_level": {round(sev.score)},\n'
            f'  "refund_requested": {str(ref.verdict).lower()},\n'
            '  "self_reported_confidence": 0.95\n'
            "}"
        )
        schema_violation = False
        failure_mode = "단일 선택값만 반환하며 옵션 간 전체 확률 분포(Probabilities)와 보정된 연속 기대 점수(Expected Score) 산출 불가"
        simulated_latency_ms = 980.4

    return ParadigmComparisonResult(
        state_preview=state_str[:220] + ("..." if len(state_str) > 220 else ""),
        system_one_jev={
            "paradigm": "System One (TypeSafe AI Jev)",
            "execution_mechanism": "Single Parallel Pass (Non-Generative Bounded Evaluation)",
            "latency_ms": jev_res.latency_ms,
            "type_safety_guaranteed": True,
            "prompt_injection_immune": True,
            "calibrated_probabilities": True,
            "output_summary": {
                "department_choice": dept.choice,
                "department_probabilities": dept.probabilities,
                "department_confidence": dept.confidence,
                "severity_expected_score": sev.score,
                "refund_noul_prob": ref.noul,
                "security_noul_prob": sec.noul,
            },
        },
        system_two_llm={
            "paradigm": "System Two (Generative LLM + JSON Prompting)",
            "execution_mechanism": "Autoregressive Token-by-Token Prose Generation",
            "simulated_latency_ms": simulated_latency_ms,
            "type_safety_guaranteed": not schema_violation,
            "prompt_injection_immune": not has_injection,
            "calibrated_probabilities": False,
            "raw_token_output": llm_raw_output,
            "observed_risk": failure_mode,
        },
        engineering_verdict=(
            "TypeSafe AI Jev(System One)는 자유 텍스트를 생성하지 않으므로 프롬프트 인젝션으로 인한 스키마 파괴가 원천 불가능하며, "
            "모든 선택지의 확률 분포(Probabilities)와 엔트로피 기반 신뢰도(Confidence)를 단일 패스로 즉시 반환하여 "
            "안전한 if/else 소프트웨어 제어 흐름을 보장합니다."
        ),
    )

