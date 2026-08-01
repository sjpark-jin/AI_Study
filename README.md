# AI Study — 주차별 AI/아키텍처 실습 및 학습 로드맵

주 1회 AI/아키텍처 프로젝트를 직접 구축해보며 기술적 이해와 IT 기획/아키텍처 관점의 실무 체크포인트를 정리하는 커리큘럼 저장소입니다.

---

## 🛠️ 사전 준비 및 환경 세팅 가이드 (Prerequisites & Setup)

macOS 및 최신 Python 환경(PEP 668)에서는 외부 패키지 설치 시 가상환경(`venv`) 생성이 필수적입니다.
아래 순서대로 가상환경을 세팅하고 필수 의존성 패키지를 설치한 후 실행해주세요.

### 1단계: 저장소 루트 가상환경 생성 및 활성화
```bash
# 1. 저장소 루트로 이동
cd /Users/sangjin/Desktop/workspace/AI_Study

# 2. Python 가상환경 생성 (최초 1회)
python3 -m venv venv

# 3. 가상환경 활성화 (macOS / Linux)
source venv/bin/activate

# Windows 사용자의 경우:
# venv\Scripts\activate
```

### 2단계: 필수 패키지 일괄 설치
```bash
# 가상환경이 활성화된 상태에서 패키지 설치
pip install --upgrade pip
pip install -r week-03/requirements.txt
```

> 💡 **VS Code / Cursor IDE 사용 팁**:
> IDE에서 파일 상단에 `Import "fastapi" could not be resolved` 등의 빨간 줄 에러가 보인다면:
> `Cmd + Shift + P` -> `Python: Select Interpreter` 선택 -> 생성된 `./venv/bin/python`을 인터프리터로 선택하시면 에러 표시가 사라집니다.

---

## 🔑 환경변수 설정 (`.env`)
각 주차 폴더(`week-01`, `week-02`, `week-03`)에는 주요 AI API 키 이름이 사전 등록된 `.env.example` 및 `.env` 파일이 포함되어 있습니다.
필요 시 보유하신 API 키를 `.env` 파일에 기입하여 바로 연동하실 수 있으며, 키가 없어도 모든 주차는 **Mock Provider**를 통해 즉시 실습 및 테스트 가능합니다.

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `COHERE_API_KEY`
- `TAVILY_API_KEY`
- `SERPER_API_KEY`
- `GROQ_API_KEY`
- `OLLAMA_BASE_URL`

---

## 📅 주차별 학습 과제 목록 (Curriculum)

| 주차 | 주제 | 핵심 키워드 & 기술 스택 | 링크 |
|:---:|:---|:---|:---:|
| **Week 01** | **최소 RAG 챗봇 직접 구성하기** | FastAPI, ChromaDB, SentenceTransformers, Vector Embeddings | [Week 01 이동](file:///Users/sangjin/Desktop/workspace/AI_Study/week-01/README.md) |
| **Week 02** | **RAG + LLM 연동 및 프롬프트/메모리 고도화** | LLM Provider (Mock/OpenAI), Reranking, Session Memory, Guardrails | [Week 02 이동](file:///Users/sangjin/Desktop/workspace/AI_Study/week-02/README.md) |
| **Week 03** | **AI Agent & Function Calling 구축** | ReAct Pattern, Tool Execution, DB/Email/RAG Integration, `.env` Setup | [Week 03 이동](file:///Users/sangjin/Desktop/workspace/AI_Study/week-03/README.md) |

---

## 🚀 주차별 실행 가이드 (Quick Start)

가상환경(`source venv/bin/activate`)이 활성화된 상태에서 실행하고자 하는 주차 폴더로 이동 후 실행합니다.

### Week 01 실행 (최소 RAG)
```bash
source venv/bin/activate
cd week-01
uvicorn app.main:app --reload
# 접속: http://127.0.0.1:8000/docs
```

### Week 02 실행 (RAG + LLM + Memory)
```bash
source venv/bin/activate
cd week-02
uvicorn app.main:app --reload
# 접속: http://127.0.0.1:8000/docs
```

### Week 03 실행 (AI Agent & Function Calling)
```bash
source venv/bin/activate
cd week-03
uvicorn app.main:app --reload
# 접속: http://127.0.0.1:8000/docs
```

---

## 💡 저장소 운영 규칙 (`drafts/`)
- 매주 토요일 GitHub Actions 워크플로(`.github/workflows/weekly-publish.yml`)가 `drafts/` 창고에 준비된 다음 주차 학습 내용을 루트로 자동으로 공개 발행합니다.
