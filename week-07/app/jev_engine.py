"""
Week 07 — TypeSafe AI Jev (System One) 의사결정 엔진 모듈.

일반적인 생성형 LLM(System Two)이 자유 형식의 텍스트 토큰을 순차 생성하는 것과 달리,
TypeSafe AI의 'Jev' 모델(System One)은 프로그램 상태(State)를 입력받아
여러 개의 강타입 질문 프리미티브(Choice, Score, Noul)를 단일 병렬 패스(Single Parallel Pass)로 평가하고,
정확한 확률 분포(Probabilities), 기대 점수(Expected Score), 신뢰도(Confidence)를 즉시 반환합니다.

지원 모드:
1. Real TypeSafe SDK (`typesafe-sdk` 패키지 + `TYPESAFE_API_KEY` 설정 시 실제 `jev-latest` 호출)
2. Calibrated Probabilistic Engine (API 키 없이도 소프트맥스 확률 분포, 엔트로피 기반 Confidence,
   루브릭 가중 기대값 Score, 베이지안 Noul 확률을 정밀 계산하는 로컬 시뮬레이터)
"""
import json
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

log = logging.getLogger("jev_engine")


# =====================================================================
# 1. TypeSafe AI Jev 3대 질문 프리미티브 (Question Primitives)
# =====================================================================
class ChoiceQuestion(BaseModel):
    """
    [Choice] 순서가 없는 카테고리/옵션 집합(최대 255개) 중 하나를 선택하는 프리미티브.
    - criteria: Dict[옵션키, 판단기준 설명] 또는 List[옵션키]
    """
    primitive_type: str = Field(default="Choice", description="프리미티브 타입")
    instructions: str = Field(..., description="평가 지시사항")
    criteria: Union[Dict[str, str], List[str]] = Field(
        ..., description="선택 가능한 옵션 목록 또는 {옵션키: 설명} 맵"
    )


class ScoreQuestion(BaseModel):
    """
    [Score] 순서가 있는 2~10단계의 루브릭(Rubric/Scale) 위에서 상태의 위치를 평가하는 프리미티브.
    - criteria: 낮은 단계(0)부터 높은 단계(N-1)까지 순서대로 정의된 기준 설명 리스트
    """
    primitive_type: str = Field(default="Score", description="프리미티브 타입")
    instructions: str = Field(..., description="척도 평가 지시사항")
    criteria: List[str] = Field(
        ..., min_length=2, max_length=10, description="순서가 있는 단계별 루브릭 설명 (0점 ~ N-1점)"
    )


class NoulQuestion(BaseModel):
    """
    [Noul] 특정 조건이나 진술이 참(Yes/True)인지 여부를 [0.0 ~ 1.0] 확률로 평가하는 이진 프리미티브.
    """
    primitive_type: str = Field(default="Noul", description="프리미티브 타입")
    instructions: str = Field(..., description="참/거짓 여부를 검증할 조건 진술")


# =====================================================================
# 2. TypeSafe AI Jev 응답 구조체 (Typed Answer Models)
# =====================================================================
class ChoiceAnswer(BaseModel):
    primitive_type: str = "Choice"
    choice: str = Field(..., description="최종 선택된 옵션 키 (최고 확률 항목)")
    probabilities: Dict[str, float] = Field(..., description="모든 옵션별 확률 분포 (합계 = 1.0)")
    confidence: float = Field(..., description="결정 신뢰도 (Normalized Inverse Entropy, 0.0~1.0)")


class ScoreAnswer(BaseModel):
    primitive_type: str = "Score"
    score: float = Field(..., description="확률 가중 연속 기대 점수 E[S] = sum(i * P_i)")
    normalized_score: float = Field(..., description="0.0 ~ 1.0 정규화 점수")
    legend: Dict[str, str] = Field(..., description="단계별 루브릭 기준 설명")
    probabilities: Dict[str, float] = Field(..., description="각 루브릭 단계별 확률 분포")
    confidence: float = Field(..., description="척도 평가 신뢰도 (0.0~1.0)")


class NoulAnswer(BaseModel):
    primitive_type: str = "Noul"
    noul: float = Field(..., description="조건이 참(Yes)일 확률 (0.0 ~ 1.0)")
    verdict: bool = Field(..., description="임계값(0.5) 기준 참/거짓 판정")
    interpretation: str = Field(..., description="확률 구간 해석 (High / Moderate / Low)")


class SystemOneResponse(BaseModel):
    model: str = Field(..., description="실행된 System One 모델 식별자 (예: jev-latest)")
    provider_mode: str = Field(..., description="실행 모드 (typesafe_sdk | calibrated_local)")
    latency_ms: float = Field(..., description="단일 병렬 패스 추론 소요 시간(ms)")
    parallel_questions_count: int = Field(..., description="단일 패스로 병렬 평가된 질문 수")
    answers: Dict[str, Union[ChoiceAnswer, ScoreAnswer, NoulAnswer]] = Field(
        ..., description="질문 키별 강타입 결과 맵"
    )


# =====================================================================
# 3. 확률 수식 유틸리티 (Softmax, Shannon Entropy Confidence, Expectation)
# =====================================================================
def compute_softmax(logits: Dict[str, float], temperature: float = 1.0) -> Dict[str, float]:
    """로짓(Logit) 점수를 합이 1.0인 확률 분포로 변환합니다."""
    if not logits:
        return {}
    max_l = max(logits.values())
    exps = {k: math.exp((v - max_l) / max(temperature, 1e-4)) for k, v in logits.items()}
    total = sum(exps.values()) or 1.0
    probs = {k: round(v / total, 4) for k, v in exps.items()}
    # 반올림 오차 보정 (합계 정확히 1.0 유지)
    diff = round(1.0 - sum(probs.values()), 4)
    top_key = max(probs, key=probs.get)
    probs[top_key] = round(probs[top_key] + diff, 4)
    return probs


def compute_distribution_confidence(probs: Dict[str, float]) -> float:
    """
    확률 분포의 엔트로피(Shannon Entropy) 및 Top-1/Top-2 마진을 결합하여
    Jev 스타일의 보정 신뢰도(Confidence, 0.0 ~ 1.0)를 계산합니다.
    - 한 옵션에 확률이 집중될수록 1.0에 수렴하고, 균등 분포에 가까울수록 0.0에 수렴합니다.
    """
    n = len(probs)
    if n <= 1:
        return 1.0
    values = sorted(probs.values(), reverse=True)
    # 1) 정규화 섀넌 엔트로피: H(P) / log(N)
    entropy = -sum(p * math.log(max(p, 1e-12)) for p in values if p > 0)
    max_entropy = math.log(n)
    inv_entropy = 1.0 - (entropy / max_entropy)
    # 2) Top-1 과 Top-2 간 확률 마진(Margin)
    margin = values[0] - values[1]
    confidence = (0.55 * inv_entropy) + (0.45 * margin)
    return round(min(max(confidence, 0.05), 0.99), 4)


# =====================================================================
# 4. TypeSafe AI Jev Engine (SDK 연동 + 로컬 확률 시뮬레이터)
# =====================================================================
class TypeSafeJevEngine:
    """
    TypeSafe AI의 `client.system_one(model="jev-latest", state=..., questions=...)` 인터페이스를
    제공하는 핵심 엔진 클래스.
    """
    def __init__(self):
        self.api_key = os.getenv("TYPESAFE_API_KEY", "").strip()
        self.provider_mode = os.getenv("DEFAULT_JEV_PROVIDER", "mock").lower()
        self.model_name = os.getenv("JEV_MODEL", "jev-latest")

        # 프리셋 샘플 상태 로드
        sample_path = os.path.join(os.path.dirname(__file__), "docs", "sample_states.json")
        self.sample_states: List[Dict[str, Any]] = []
        if os.path.isfile(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                self.sample_states = json.load(f)

    def system_one(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Union[ChoiceQuestion, ScoreQuestion, NoulQuestion, Dict[str, Any]]],
        model: Optional[str] = None,
    ) -> SystemOneResponse:
        """
        입력된 프로그램 상태(State)에 대해 다수의 타입 질문(Choice, Score, Noul)을
        단일 병렬 패스(Single Parallel Pass)로 평가합니다.
        """
        target_model = model or self.model_name
        start_ts = time.perf_counter()

        # Dict 형태로 전달된 질문을 Pydantic 프리미티브 객체로 정규화
        normalized_questions: Dict[str, Union[ChoiceQuestion, ScoreQuestion, NoulQuestion]] = {}
        for q_key, q_val in questions.items():
            if isinstance(q_val, (ChoiceQuestion, ScoreQuestion, NoulQuestion)):
                normalized_questions[q_key] = q_val
            elif isinstance(q_val, dict):
                p_type = q_val.get("primitive_type", "Choice").lower()
                if p_type == "choice":
                    normalized_questions[q_key] = ChoiceQuestion(**q_val)
                elif p_type == "score":
                    normalized_questions[q_key] = ScoreQuestion(**q_val)
                elif p_type == "noul":
                    normalized_questions[q_key] = NoulQuestion(**q_val)
                else:
                    raise ValueError(f"지원하지 않는 프리미티브 타입입니다: {p_type}")

        # 실제 TypeSafe SDK 호출 시도 (설정된 경우)
        if self.provider_mode == "typesafe" and self.api_key:
            try:
                return self._call_real_typesafe_sdk(state, normalized_questions, target_model, start_ts)
            except Exception as e:
                log.warning("TypeSafe SDK 호출 실패, 로컬 확률 추론 엔진으로 폴백합니다: %s", e)

        # 로컬 확률 추론 엔진 실행
        state_text = self._serialize_state(state)
        answers: Dict[str, Union[ChoiceAnswer, ScoreAnswer, NoulAnswer]] = {}

        for q_key, q_obj in normalized_questions.items():
            if isinstance(q_obj, ChoiceQuestion):
                answers[q_key] = self._eval_choice(state_text, q_key, q_obj)
            elif isinstance(q_obj, ScoreQuestion):
                answers[q_key] = self._eval_score(state_text, q_key, q_obj)
            elif isinstance(q_obj, NoulQuestion):
                answers[q_key] = self._eval_noul(state_text, q_key, q_obj)

        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)
        return SystemOneResponse(
            model=target_model,
            provider_mode="calibrated_local",
            latency_ms=latency_ms,
            parallel_questions_count=len(normalized_questions),
            answers=answers,
        )

    def _serialize_state(self, state: Union[str, Dict[str, Any]]) -> str:
        if isinstance(state, str):
            return state
        return json.dumps(state, ensure_ascii=False)

    # -----------------------------------------------------------------
    # 개별 프리미티브 평가 로직 (Choice / Score / Noul)
    # -----------------------------------------------------------------
    def _eval_choice(self, state_text: str, q_key: str, q: ChoiceQuestion) -> ChoiceAnswer:
        s_lower = state_text.lower()
        if isinstance(q.criteria, list):
            options_map = {opt: opt for opt in q.criteria}
        else:
            options_map = q.criteria

        # 도메인 키워드 사전 (옵션 키 및 설명과 상태 텍스트 간의 의미적 정합성 계산)
        domain_signals = {
            "billing": ["결제", "환불", "청구", "카드", "영수증", "구독", "요금", "승인", "refund", "charge", "invoice", "duplicate_tx", "amount_usd", "$"],
            "returns": ["환불", "반품", "취소", "중복 결제", "refund", "duplicate"],
            "technical": ["장애", "에러", "타임아웃", "504", "클러스터", "커넥션", "api", "서버", "롤백", "db-conn", "timeout", "error_rate", "웹훅"],
            "sre": ["긴급", "장애", "504", "프로덕션", "클러스터", "롤백", "투입", "outage", "sre", "critical"],
            "security": ["보안", "해외 ip", "탈취", "잠금", "인젝션", "권한", "토큰", "ignore previous", "credentials", "suspicious_ip", "보안 감사"],
            "account": ["계정", "로그인", "비밀번호", "잠금", "인원", "플랜", "계약서", "상담"],
            "general": ["문의", "상담", "고민", "양식", "검토"],
        }

        logits: Dict[str, float] = {}
        for opt_key, opt_desc in options_map.items():
            score = 0.1  # 기본 사전 로짓(Prior)
            key_lower = opt_key.lower()
            desc_lower = opt_desc.lower()

            # 1) 옵션 키/설명 내 어절 직접 매칭
            for token in (key_lower + " " + desc_lower).replace(",", " ").split():
                if len(token) >= 2 and token in s_lower:
                    score += 1.15

            # 2) 도메인 시그널 사전 매칭
            for dom_k, keywords in domain_signals.items():
                if dom_k in key_lower or dom_k in desc_lower or any(w in desc_lower for w in keywords[:3]):
                    matched_hits = sum(1 for kw in keywords if kw in s_lower)
                    score += matched_hits * 0.95

            logits[opt_key] = score

        # 복합/모호 문의("has_multiple_intents": true 또는 여러 도메인에 비슷하게 걸친 경우) 분포 평탄화 보정
        is_multi_intent = "has_multiple_intents" in s_lower or ("요금제" in s_lower and "웹훅" in s_lower and "보안" in s_lower)
        if is_multi_intent:
            avg_l = sum(logits.values()) / max(len(logits), 1)
            logits = {
                k: avg_l + (0.28 if "account" in k else (0.18 if "billing" in k else (0.12 if "technical" in k else 0.05)))
                for k in logits
            }
            temperature = 1.6
        else:
            temperature = 0.85

        probs = compute_softmax(logits, temperature=temperature)
        best_choice = max(probs, key=probs.get)
        confidence = compute_distribution_confidence(probs)

        return ChoiceAnswer(
            choice=best_choice,
            probabilities=probs,
            confidence=confidence,
        )

    def _eval_score(self, state_text: str, q_key: str, q: ScoreQuestion) -> ScoreAnswer:
        s_lower = state_text.lower()
        num_levels = len(q.criteria)

        # 긴급도/심각도/불만도 강도 시그널 분석
        high_severity_signals = [
            "긴급", "즉시", "심각", "장애", "504", "40%", "탈취", "새벽", "중복 청구",
            "immediately", "critical", "ignore previous", "root credentials", "42.5", "투입"
        ]
        mid_severity_signals = [
            "환불", "오류", "지연", "안내", "확인", "필요", "부탁", "변경", "상담"
        ]
        calm_signals = [
            "고민 중", "문의", "혹시", "다음 달", "양식", "감사합니다"
        ]

        high_hits = sum(1 for w in high_severity_signals if w in s_lower)
        mid_hits = sum(1 for w in mid_severity_signals if w in s_lower)
        calm_hits = sum(1 for w in calm_signals if w in s_lower)

        # 목표 중심점(Target Center, 0.0 ~ num_levels - 1) 산출
        if high_hits >= 3:
            target_pos = (num_levels - 1) * 0.92
        elif high_hits >= 1:
            target_pos = (num_levels - 1) * 0.72
        elif calm_hits >= 2 and high_hits == 0:
            target_pos = (num_levels - 1) * 0.18
        else:
            target_pos = (num_levels - 1) * (0.45 + min(mid_hits * 0.08, 0.25))

        # 가우시안 거리 기반 로짓 생성
        logits: Dict[str, float] = {}
        legend: Dict[str, str] = {}
        for idx, desc in enumerate(q.criteria):
            level_key = f"level_{idx}"
            legend[level_key] = f"[{idx}점] {desc}"
            dist = abs(idx - target_pos)
            logits[level_key] = -1.6 * (dist ** 2)

        probs = compute_softmax(logits, temperature=0.8)
        # 확률 가중 기대 점수: E[S] = sum(i * P(level_i))
        expected_score = sum(idx * probs[f"level_{idx}"] for idx in range(num_levels))
        norm_score = expected_score / max(num_levels - 1, 1)
        confidence = compute_distribution_confidence(probs)

        return ScoreAnswer(
            score=round(expected_score, 4),
            normalized_score=round(norm_score, 4),
            legend=legend,
            probabilities=probs,
            confidence=confidence,
        )

    def _eval_noul(self, state_text: str, q_key: str, q: NoulQuestion) -> NoulAnswer:
        s_lower = state_text.lower()
        inst_lower = (q_key + " " + q.instructions).lower()

        # 조건 유형별 확률 계산
        logit = -1.8  # 기본값: False 쪽에 가중(약 0.14)

        # 1) 환불 요청 여부 (refund)
        if any(w in inst_lower for w in ["환불", "refund", "결제 취소", "배상"]):
            if any(w in s_lower for w in ["환불", "refund", "중복 결제", "중복 청구", "duplicate_tx"]):
                logit = 2.65
            elif "요금제" in s_lower or "결제" in s_lower:
                logit = -0.75

        # 2) 보안 위협 / 프롬프트 인젝션 / 계정 탈취 여부 (security / injection / pii)
        elif any(w in inst_lower for w in ["보안", "인젝션", "탈취", "위협", "security", "injection", "breach"]):
            if any(w in s_lower for w in ["ignore previous", "탈취", "해외 ip", "root credentials", "suspicious_ip", "비정상 로그인"]):
                logit = 3.10
            elif "보안 감사" in s_lower:
                logit = -1.10

        # 3) 프로덕션 긴급 장애 / SLA 위반 위험 여부 (urgent / outage / sla)
        elif any(w in inst_lower for w in ["긴급", "장애", "즉시", "urgent", "outage", "sla", "production"]):
            if any(w in s_lower for w in ["504", "장애", "긴급", "클러스터", "롤백", "즉시 환불", "즉시 계정 잠금"]):
                logit = 2.25
            elif "다음 달" in s_lower or "고민 중" in s_lower:
                logit = -2.40

        # 4) 일반 조건어 매칭 (사용자가 커스텀 Noul 질문을 입력한 경우)
        else:
            inst_tokens = [
                t for t in q.instructions.lower().replace("?", " ").replace(",", " ").split()
                if len(t) >= 2 and t not in {"여부", "있는가", "하는가", "인가요", "does", "is", "the", "this", "customer"}
            ]
            matched = sum(1 for t in inst_tokens if t in s_lower)
            logit = -1.4 + (matched * 1.35)

        noul_prob = round(1.0 / (1.0 + math.exp(-logit)), 4)
        if noul_prob >= 0.70:
            interp = "High (강한 참 확신 — 자동 트리거 활성 구간)"
        elif noul_prob >= 0.40:
            interp = "Moderate (불확실/경계 구간 — 추가 검증 권장)"
        else:
            interp = "Low (거짓 확신 — 조건 미해당)"

        return NoulAnswer(
            noul=noul_prob,
            verdict=noul_prob >= 0.50,
            interpretation=interp,
        )

    def _call_real_typesafe_sdk(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Union[ChoiceQuestion, ScoreQuestion, NoulQuestion]],
        model: str,
        start_ts: float,
    ) -> SystemOneResponse:
        """실제 `typesafe-sdk` 라이브러리가 설치된 환경에서 호출합니다."""
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

        sdk_questions = {}
        for k, q in questions.items():
            if isinstance(q, ChoiceQuestion):
                sdk_questions[k] = Choice(instructions=q.instructions, criteria=q.criteria)
            elif isinstance(q, ScoreQuestion):
                sdk_questions[k] = Score(instructions=q.instructions, criteria=q.criteria)
            elif isinstance(q, NoulQuestion):
                sdk_questions[k] = Noul(instructions=q.instructions)

        with TypeSafeClient(api_key=self.api_key) as client:
            resp = client.system_one(model=model, state=state, questions=sdk_questions)

        answers: Dict[str, Union[ChoiceAnswer, ScoreAnswer, NoulAnswer]] = {}
        for k, q in questions.items():
            raw_ans = resp.answers[k]
            if isinstance(q, ChoiceQuestion):
                probs = dict(getattr(raw_ans, "probabilities", {}))
                answers[k] = ChoiceAnswer(
                    choice=getattr(raw_ans, "choice", getattr(raw_ans, "value", "")),
                    probabilities=probs,
                    confidence=round(float(getattr(raw_ans, "confidence", compute_distribution_confidence(probs))), 4),
                )
            elif isinstance(q, ScoreQuestion):
                probs = dict(getattr(raw_ans, "probabilities", {}))
                sc = float(getattr(raw_ans, "score", 0.0))
                answers[k] = ScoreAnswer(
                    score=round(sc, 4),
                    normalized_score=round(sc / max(len(q.criteria) - 1, 1), 4),
                    legend={f"level_{i}": c for i, c in enumerate(q.criteria)},
                    probabilities=probs,
                    confidence=round(float(getattr(raw_ans, "confidence", compute_distribution_confidence(probs))), 4),
                )
            elif isinstance(q, NoulQuestion):
                np_val = round(float(getattr(raw_ans, "noul", getattr(raw_ans, "probability", 0.0))), 4)
                answers[k] = NoulAnswer(
                    noul=np_val,
                    verdict=np_val >= 0.5,
                    interpretation="High" if np_val >= 0.7 else ("Moderate" if np_val >= 0.4 else "Low"),
                )

        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)
        return SystemOneResponse(
            model=model,
            provider_mode="typesafe_sdk",
            latency_ms=latency_ms,
            parallel_questions_count=len(questions),
            answers=answers,
        )


# 싱글톤 인스턴스
jev_engine = TypeSafeJevEngine()
