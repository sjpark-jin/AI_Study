# Week 06 — Advanced Hybrid RAG Pipeline & RAG 정량 평가 시스템

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 6주차 주제는 **Advanced Hybrid RAG(BM25 + Dense Vector + Reranker) 및 RAG 정량 평가**.

## 이번 주에 하고 싶었던 것
단일 Dense Vector 임베딩 검색이 가지는 고질적인 문제(사내 시스템 에러코드, 모델명, 규정 조항 등 고유명사 검색 누락)를 극복하기 위해, **BM25 키워드 검색과 Dense Vector 의미 검색을 RRF(Reciprocal Rank Fusion)로 결합하고 Cross-Encoder Reranker로 재순위화하는 4단계 고급 RAG 파이프라인**을 구축하는 것. 
또한 검색 및 생성된 답변의 신뢰성을 보장하기 위해 **Ragas 3대 지표(Faithfulness, Answer Relevance, Context Precision) 정량 평가 체계**와 이를 실시간으로 비교 체험할 수 있는 **대화형 인터랙티브 웹 포털**을 구현하는 것.

---

## 🛠️ 사전 준비 및 환경 세팅

실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화합니다:

```bash
# 1. 저장소 루트로 이동
cd /Users/sangjin/Desktop/workspace/AI_Study

# 2. 가상환경 활성화 (macOS / Linux)
source venv/bin/activate

# 3. 6주차 폴더로 이동 및 서버 실행
cd week-06
uvicorn app.main:app --reload

# 4. 브라우저 접속
# 대화형 학습 웹 UI: http://127.0.0.1:8000
# Swagger API 문서: http://127.0.0.1:8000/docs
```

---

## 주요 기능

1. **4단계 Advanced Hybrid Retrieval (`hybrid_search.py`, `reranker.py`)**:
   - **BM25 키워드 검색**: 복합어 및 특수 에러코드(`K8S-INGRESS-404`, `AUTH-JWT-V2`) 정확 매칭.
   - **Dense Vector 검색**: ChromaDB + SentenceTransformers 기반 문맥적 의미 유사도 탐색.
   - **RRF (Reciprocal Rank Fusion, k=60)**: 점수 척도 차이를 상쇄하는 순위 기반 하이브리드 결합.
   - **Cross-Encoder Reranker**: 질문과 문서를 결합하여 정밀 토큰 레벨 연관도 재채점.

2. **RAG 정량 평가 시스템 (Ragas 3대 지표) (`rag_evaluator.py`)**:
   - **Faithfulness (충실도)**: 생성된 답변이 검색 문맥 내 사실에만 기반하는지 검증 (환각 차단).
   - **Answer Relevance (답변 관련성)**: 생성된 답변이 질문의 목적과 지시사항에 부합하는지 평가.
   - **Context Precision (문맥 정확도)**: 질문 해결에 가장 중요한 문서가 검색 상위에 위치했는지 평가.

3. **대화형 인터랙티브 학습 포털 (`app/static/index.html`)**:
   - **4분할 검색 비교기**: BM25 vs Dense Vector vs RRF vs Reranker 순위 변화 실시간 확인.
   - **RAG 실시간 평가기**: 답변 생성과 함께 Ragas 3대 지표 점수판 즉시 시각화.
   - **학습 허브**: 10가지 트러블슈팅 실수 노트 및 1~6주차 전체 로드맵 내장.

---

## 구성

```
week-06/
├── PLANNING.md          # 6주차 아키텍처, 10가지 실수 노트, 재학습 가이드 ★
├── requirements.txt     # 의존성 패키지 명세
├── .env.example         # 환경변수 템플릿
├── .env                 # 로컬 환경변수 파일
├── README.md            # 주차 소개 및 실행 가이드
└── app/
    ├── main.py          # FastAPI 진입점 및 웹 UI 라우트
    ├── hybrid_search.py # BM25, Dense Vector, RRF 융합 검색기
    ├── reranker.py      # Cross-Encoder 기반 재순위화 엔진
    ├── rag_evaluator.py # Ragas 3대 지표 정량 평가기
    ├── llm.py           # Mock 및 OpenAI API 프로바이더
    ├── static/
    │   └── index.html   # 다크모드 대화형 학습 대시보드
    └── docs/
        └── sample_tech_docs.txt # 사내 기술 규격 및 장애 대응 샘플 문서
```

---

## 실행 및 테스트 예시

### 1. 4분할 하이브리드 검색 비교 (`POST /search/hybrid`)
```json
// 요청 (Request)
{
  "query": "K8S-INGRESS-404 인그레스 에러 발생 시 조치 방법",
  "top_k": 4,
  "dense_weight": 0.5,
  "bm25_weight": 0.5
}

// 응답 (Response)
{
  "query": "K8S-INGRESS-404 인그레스 에러 발생 시 조치 방법",
  "bm25_candidates": [ ... ],
  "dense_candidates": [ ... ],
  "hybrid_rrf_candidates": [ ... ],
  "reranked_final_candidates": [ ... ]
}
```

### 2. 하이브리드 RAG 생성 및 실시간 정량 평가 (`POST /rag/generate`)
```json
// 요청 (Request)
{
  "query": "AUTH-JWT-V2 통합 인증 규격과 토큰 유효시간을 알려줘.",
  "use_hybrid": true,
  "use_rerank": true
}

// 응답 (Response)
{
  "query": "AUTH-JWT-V2 통합 인증 규격과 토큰 유효시간을 알려줘.",
  "answer": "AUTH-JWT-V2 통합 인증 규격 안내입니다:\n1. 유효 시간: Access Token은 15분, Refresh Token은 7일간 유효합니다...",
  "retrieved_documents": [ ... ],
  "evaluation": {
    "overall_score": 91,
    "is_passed": true,
    "faithfulness": { "name": "Faithfulness", "score": 95, "is_passed": true },
    "answer_relevance": { "name": "Answer Relevance", "score": 90, "is_passed": true },
    "context_precision": { "name": "Context Precision", "score": 88, "is_passed": true },
    "actionable_feedback": "RAG 파이프라인이 3대 핵심 품질 기준을 모두 훌륭하게 만족합니다."
  }
}
```

---

## 직접 해보며 배운 것

- **실무에서 단일 Vector 검색만 쓰면 반드시 장애가 난다**: 아무리 거대한 임베딩 모델이라도 하이픈이 들어간 에러 코드나 사내 고유 약어는 OOV나 차원 압축으로 인해 유사도가 뭉개진다. BM25를 병합하고 RRF로 순위를 묶는 순간 검색 실패율이 획기적으로 떨어진다.
- **Reranker는 소수 후보군에만 국소적으로 써야 한다**: Cross-Encoder는 Bi-Encoder보다 훨씬 정교하지만 연산 비용이 크다. 1차 하이브리드 검색으로 상위 4~8개만 추리고 여기에만 Reranker를 태워야 실무 허용 Latency(200~500ms 이내)를 지킬 수 있다.
- **RAG 평가는 '삼총사(Faithfulness, Relevance, Precision)'로 쪼개야 병목이 보인다**: 단순 종합 점수만 보면 검색 문제인지, 프롬프트 환각 문제인지 알 수 없다. 3개 축으로 분리해야 "문맥은 잘 찾았는데 LLM이 헛소리를 하는지(Faithfulness 결함)" 아니면 "엉뚱한 문서를 찾아서 답변도 빗나갔는지(Precision 결함)"를 즉시 진단할 수 있다.
