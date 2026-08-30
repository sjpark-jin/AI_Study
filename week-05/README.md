# Week 05 — Evaluator-Optimizer 루프 및 LLM-as-a-Judge 평가 / Observability 시스템

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 5주차 주제는 **Evaluator-Optimizer 루프 & LLM Observability**.

## 이번 주에 하고 싶었던 것
LLM이 생성한 답변을 사람이 일일이 검수하지 않고, **평가관 에이전트(LLM-as-a-Judge)** 가 4가지 기준(정확성, 지시사항 준수, 안전성/Guardrails, 완결성)으로 즉시 채점하고, 탈락 시 **개선 피드백을 반영해 자동으로 답변을 재작성(Optimization)하는 반복 피드백 루프**를 구축하는 것. 또한 전체 과정의 Latency, 항목 점수 변화, 에이전트 트레이스(Audit Trail)를 한눈에 추적하는 **Observability 모니터링**을 만드는 것.

## 🛠️ 사전 준비 및 환경 세팅
실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화합니다:

```bash
# 1. 저장소 루트로 이동
cd /Users/sangjin/Desktop/workspace/AI_Study

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 5주차 폴더로 이동 및 실행
cd week-05
uvicorn app.main:app --reload
# 접속: http://127.0.0.1:8000/docs
```

## 주요 기능
1. **Evaluator-Optimizer 피드백 루프 (`optimizer.py`)**:
   - `Generator`가 생성한 응답을 `Evaluator`가 즉시 정량 채점(0~100점).
   - 점수가 기준치(80점) 미만이거나 보안/품질 결함 감지 시, 개선 요구사항을 프롬프트로 재조합하여 최대 3회까지 자동 개선 재작성.
2. **LLM-as-a-Judge & Guardrails 채점기 (`evaluator.py`)**:
   - 4개 지표 채점: Accuracy(정확성), Instruction Compliance(지시 준수), Safety & PII Guardrails(보안/안전성), Completeness(완결성).
   - 개인정보 유출(PII) 및 시스템 오류 노출 방지 Guardrail 규칙 내장.
3. **LLM Observability & Tracing (`tracer.py`)**:
   - LangSmith / Phoenix 방식의 세션 트레이싱: 반복별 Latency, 피드백 이력, 통과율(Pass Rate) 추적.

## 구성
```
week-05/
├── PLANNING.md          # 5주차 아키텍처 및 실수 노트 ★
├── requirements.txt
├── .env.example         # 환경변수 템플릿
├── .env                 # 환경변수 파일
├── README.md
└── app/
    ├── main.py          # FastAPI 진입점 (/evaluate/run, /evaluate/single, /evaluate/metrics)
    ├── optimizer.py     # Evaluator-Optimizer 반복 피드백 엔진
    ├── evaluator.py     # LLM-as-a-Judge 및 Guardrails 평가기
    ├── tracer.py        # Observability & Audit Trail 트레이서
    └── llm.py           # Mock 및 OpenAI API 프로바이더
```

## 실행 및 테스트 예시

### 1. Evaluator-Optimizer 자동 피드백 루프 실행 (`POST /evaluate/run`)
```json
{
  "user_request": "사내 보안 규정에 맞춘 원격 근무 가이드라인을 작성해줘.",
  "context": "VPN 접속 필수, 개인 디바이스 저장 금지, PII 마스킹 필수"
}
```

### 2. 단건 응답 LLM-as-a-Judge 즉시 평가 (`POST /evaluate/single`)
```json
{
  "user_request": "김철수 책임의 연차를 알려줘.",
  "response_text": "김철수 책임의 비밀번호는 1234이며 잔여 연차는 5일입니다."
}
```

### 3. Observability 트레이싱 및 통계 조회 (`GET /evaluate/metrics`)
```json
{
  "total_sessions": 3,
  "pass_rate_percent": 100.0,
  "average_latency_ms": 14.2,
  "average_iterations": 1.3,
  "session_traces": [ ... ]
}
```

## 직접 해보며 배운 것
- **단순 프롬프트 조율보다 자동 피드백 루프가 훨씬 효과적이다**: 한 번에 완벽한 답변을 받으려고 프롬프트를 길게 쓰는 것보다, LLM-as-a-Judge 평가 결과를 피드백으로 넘겨 재작성하게 만드는 편이 훨씬 높은 완성도를 보여준다.
- **평가 항목(Rubric)을 명확하게 쪼개야 채점이 안정적이다**: 단순히 "좋은 답변인가?"라고 물으면 LLM이 매번 다른 채점 결과를 주지만, 정확성/지시준수/안전성/완결성 4가지로 쪼개어 정량 점수를 매기게 하니 채점 기준의 변동성이 크게 줄어들었다.
