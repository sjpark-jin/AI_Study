# Week 01 — 최소 RAG 챗봇 직접 구성해보기 (FastAPI + ChromaDB)

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 1주차 주제는 RAG.

## 이번 주에 하고 싶었던 것
"사내 문서 기반 챗봇 만들자"는 말이 실제로 어떤 컴포넌트로 쪼개지는지 손으로 확인하고 싶었다.
그래서 가장 얇은 RAG 파이프라인을 직접 세워보기로 했다: `문서 → 임베딩 → 벡터DB 검색 → 답변`.

## 🛠️ 사전 준비 및 환경 세팅 (Prerequisites & Installation)
실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화하고 필요 의존성 패키지를 설치합니다:

```bash
# 1. 저장소 루트로 이동 및 가상환경 생성 (최초 1회)
cd /Users/sangjin/Desktop/workspace/AI_Study
python3 -m venv venv

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 필수 패키지 설치
pip install -r week-01/requirements.txt
```

## 구성
```
week-01/
├── PLANNING.md          # 구성하며 정리한 아키텍처 + 직접 밟은 실수 노트 ★
├── requirements.txt     # 필요 패키지 목록
├── .env.example         # 환경변수 템플릿
├── .env                 # 환경변수 파일
├── README.md
└── app/
    ├── main.py          # FastAPI 진입점 (/chat)
    ├── rag.py           # 인제스트 + 검색 코어
    └── docs/            # 지식베이스 (.txt)
```

## 실행
```bash
# 가상환경 활성화 후 실행
source venv/bin/activate
cd week-01
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs 에서 POST /chat 테스트
```

## 직접 해보며 배운 것
- **add로 인제스트하니 재기동마다 문서가 중복 누적**됐다. 내용 해시를 ID로 써서 upsert로 바꾸니 해결.
- 처음엔 문서와 질문을 **다른 임베딩 모델로 돌려서** 검색이 계속 엉뚱한 걸 물어왔다. 같은 모델로 통일.
- Chroma가 돌려주는 게 유사도가 아니라 **거리**라 방향을 반대로 필터링해서 한참 헤맸다.
- top-k는 관련 문서가 없어도 **뭐든 반환**한다는 걸 뒤늦게 알았다. 거리 임계값으로 컷하도록 수정.

## 다음 주 계획
검색까지만 붙였으니, 다음엔 실제 LLM을 연결해 답변 생성 단계를 제대로 만들어볼 예정.
