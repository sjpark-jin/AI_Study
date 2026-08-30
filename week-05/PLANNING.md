# Week 05 — Evaluator-Optimizer 루프 및 LLM-as-a-Judge 평가 / Observability 시스템

## 1. 한 줄 요약
LLM이 생성한 응답을 **평가관(LLM-as-a-Judge)** 이 즉시 채점하고, 통과 실패 시 **피드백을 반영해 자동으로 답변을 재작성(Optimization)** 하는 반복 루프와, 이 모든 과정을 실시간 트레이스로 추적하는 **Observability 모니터링 시스템**을 구축했다.

## 2. 왜 Evaluator-Optimizer & Observability인가? (실무 관점)
- **단발성 Prompt Engineering의 한계**: 사용자의 질문이 다양해질수록 단 한 번의 LLM 프롬프트 요청만으로 모든 조건(보안, 양식, 근거, 완결성)을 100% 만족시키기 어렵다.
- **LLM-as-a-Judge 패턴의 필요성**: 사람의 개입 없이 AI가 생성한 결과를 다른 AI(또는 규정 검수 프로세스)가 평가관으로서 객관적인 정량 점수(Rubric Score)와 개선 요구사항을 산출한다.
- **Evaluator-Optimizer 루프**: "생성(Generate) → 채점(Evaluate) → 피드백 반영 재작성(Optimize)" 피드백 고리를 연결하여 요구 품질을 충족할 때까지 자율 개선한다.
- **Observability (가시성 & Audit Trail)**: 몇 번의 루프를 거쳤는지, Latency는 얼마나 늘어났는지, 어떤 피드백으로 점수가 상승했는지 추적할 수 없는 AI 서비스는 운용 및 검증이 불가능하다.

## 3. 구조 (아키텍처)
```
[사용자 요청 / 문맥]
       │
       ▼
 ┌──────────────┐     답변 생성 (Iteration 1..N)
 │ Generator    │ ───────────────────────────────┐
 └──────────────┘                                │
       ▲                                         ▼
       │                                 ┌───────────────┐
       │ 피드백 반영 재작성              │ Evaluator     │  (LLM-as-a-Judge & Guardrails)
       │ (Score < 80)                    └───────────────┘
       │                                         │
       ├─────────────────────────────────────────┤  점수 채점 및 피드백 산출
       │                                         ▼
       │                                 ┌───────────────┐
       │                                 │ Score & Pass? │
       │                                 └───────────────┘
       │                                   │          │
       │  NO (Score < 80, iter < max)     │          │ YES (Score >= 80)
       └──────────────────────────────────┘          ▼
                                              ┌───────────────┐
                                              │ FINISH        │
                                              └───────────────┘
                                                     │
                                                     ▼
                                        [ExecutionTracer & Metrics]
                                         - Iteration History
                                         - Latency Breakdown
                                         - Audit Logs
```

## 4. 실행 방법
```bash
cd week-05
source ../venv/bin/activate
uvicorn app.main:app --reload
# 브라우저: http://127.0.0.1:8000/docs 에서 테스트
```

## 5. 만들어보며 겪은 실수 노트 (중요)

> 코드를 짜면서 막혔던 지점들과 해결 방법입니다.

| # | 문제 현상 | 왜 발생했나? | 이렇게 해결함 |
|---|-----------|--------------|---------------|
| 1 | **Evaluator가 항상 100점을 줌** | 평가 프롬프트가 너무 관대하거나 채점 기준(Rubric)이 모호함 | 정확성, 지시준수, 안전성, 완결성 4개 세부 항목으로 나누고 정량 점수를 강제 |
| 2 | **Optimizer 루프가 무한히 반복됨** | 피드백 반영 후에도 점수가 기준치에 달하지 못함 | `MAX_OPTIMIZE_ITERATIONS = 3` 으로 최대 재시도 횟수 제한 설정 |
| 3 | **피드백 반영 시 이전 답변의 오류가 반복됨** | 재작성 요청 시 이전 생성 결과만 전달하고 구체적 개선 가이드를 빠뜨림 | `원래 질문 + 이전 답변 + 평가관 피드백 + 감지된 이슈`를 프롬프트에 동적 결합 |
| 4 | **LLM-as-a-Judge의 JSON 파싱 실패** | LLM 응답에 마크다운 블록(```json)이나 서론 텍스트가 섞여 나옴 | `json.loads` 전후 예외 처리 및 Pydantic 기반 폴백 구조 마련 |
| 5 | **보안 결함(PII 유출 등)을 AI가 감지하지 못함** | LLM의 정성 평가에만 의존하여 정규식/규칙 기반 검수를 놓침 | Evaluator 내부에 PII/시스템 메시지 전용 Rule-based Guardrails 병행 적용 |
| 6 | **루프 반복으로 인해 Latency가 급증함** | 1회 응답에 1초 걸리던 서비스가 3회 반복 시 5~6초 소요됨 | 세션 트레이서(`tracer.py`)를 통해 단계별 소요 시간을 기록하고 모니터링 가능하게 함 |
| 7 | **Evaluator 프롬프트 자체에 환각 발생** | 채점관 LLM이 사용자의 질문 의도를 왜곡하여 엉뚱한 피드백 전달 | 참고 문맥(Context)을 평가 프롬프트에 명시적으로 주입하여 검수 기준 고정 |
| 8 | **API 키 미설정 시 평가 시스템 기동 불가** | 외부 LLM 연동 문제로 로컬 테스트 및 CI/CD 환경 막힘 | Mock Provider에서도 평가 및 루프 동작을 즉시 검증할 수 있도록 Mock 채점 로직 설계 |
| 9 | **트레이스 데이터 누적으로 인한 메모리 증가** | 세션 트레이스를 전역 리스트에 무제한 쌓음 | `tracer_store` 크기를 최대 50개로 제한하는 링 버퍼 순환 구조로 개선 |
| 10 | **단순 통과 여부만 출력되어 개선 흐름 파악 불가** | 최종 답변만 반환되어 어느 회차에서 어떤 지적을 받아 수정되었는지 모름 | `iteration_history`에 회차별 답변, 점수, 피드백, Latency를 배열로 정교하게 반환 |

## 6. 다음 주 확장 아이디어 (Week 06)
- **Advanced RAG Pipeline & Hybrid Search**: BM25 키워드 검색과 Dense Vector 검색을 결합한 하이브리드 검색 및 Reranking 고도화
- **RAG Evaluation (Ragas / TruLens 기준)**: Context Precision, Context Recall, Faithfulness 평가 지표 추가 연동
