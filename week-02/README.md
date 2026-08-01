# Week 02 — RAG + LLM 연동 및 프롬프트/메모리/재순위 고도화

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 2주차 주제는 RAG + LLM 통합 파이프라인.

## 이번 주에 하고 싶었던 것
1주차에 구축한 단순 문서 검색(Retrieval) 파이프라인 위에 **실제 LLM 연동, 재순위(Reranking), 대화 이력 유지(Session Memory), 환각 방지 가드레일**을 결합하여 실무에 즉시 적용 가능한 수준의 RAG 아키텍처를 세우는 것.

## 🛠️ 사전 준비 및 환경 세팅 (Prerequisites & Installation)
실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화하고 필요 의존성 패키지를 설치합니다:

```bash
# 1. 저장소 루트로 이동 및 가상환경 생성 (최초 1회)
cd /Users/sangjin/Desktop/workspace/AI_Study
python3 -m venv venv

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 필수 패키지 설치
pip install -r week-02/requirements.txt
```

## 주요 기능
1. **LLM Provider 추상화 (`llm.py`)**: API 키 없이도 로컬에서 즉시 구동되는 **Mock LLM Provider** 기본 탑재 (OpenAI / Ollama 연동 지원).
2. **세션 대화 메모리 (`memory.py`)**: `session_id`별 대화 맥락을 기억하여 꼬리 질문("휴가 정책은? → 연차는 며칠이지?")에 정확히 대답.
3. **2단계 재순위 (Reranking)**: 1차 벡터 검색 후 키워드 및 유사도 가중치 재점수화를 적용하여 가장 정확한 근거 문서 선택.
4. **엄격한 환각(Hallucination) 방지**: 프롬프트 가드레일을 적용하여 지식베이스에 없는 내용은 임의로 생성하지 않고 정확하게 거절.

## 구성
```
week-02/
├── PLANNING.md          # 2주차 아키텍처 + IT 기획 실수 노트 ★
├── requirements.txt
├── .env.example         # 환경변수 템플릿
├── .env                 # 환경변수 파일
├── README.md
└── app/
    ├── main.py          # FastAPI 진입점 (/chat, /session, /health)
    ├── rag.py           # 검색 + Reranking + LLM 프롬프트 조립 코어
    ├── llm.py           # LLM 공급자 (Mock LLM / OpenAI / Ollama)
    ├── memory.py        # 대화 세션 메모리 관리
    └── docs/            # 사내 규정 샘플 지식베이스 (.txt)
        └── sample_policy.txt
```

## 실행
```bash
# 가상환경 활성화 후 실행
source venv/bin/activate
cd week-02
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs 에서 POST /chat 테스트
```

### 테스트 예시 (Curl / Swagger Docs)
```json
// POST /chat
{
  "question": "연차 휴가는 일년에 며칠 부여되나요?",
  "session_id": "user-session-123"
}
```

## 직접 해보며 배운 것
- **API 키 없이도 테스트 가능한 구조**의 중요성을 체감했다. Mock Provider가 준비되어 있어 환경변수 설정이나 API 비용 부담 없이 파이프라인 전체 흐름 검증이 가능했다.
- **Reranking과 세션 메모리**를 붙이니 1주차의 단발성 검색에 비해 대화 수준과 답변 정확도가 비약적으로 향상되었다.
- 환각 방지를 위해서는 단순 임베딩 거리에 의존하지 않고 **시스템 프롬프트의 명확한 제약조건**이 동반되어야 함을 확인했다.

## 다음 주 계획
다음 주(Week 03)에는 단순 검색/답변 생성을 넘어, 사내 DB 조회나 이메일 발송 등 실질적인 과업을 수행할 수 있는 **AI Agent & Function Calling** 개념을 도입할 예정.
