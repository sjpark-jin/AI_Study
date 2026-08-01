# Week 03 — AI Agent & Function Calling (도구 사용하는 AI 에이전트 구축)

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 3주차 주제는 **AI Agent & Function Calling**.

## 이번 주에 하고 싶었던 것
단순히 질문에 답만 하는 RAG 챗봇을 넘어, 사용자 질문을 자율적으로 해석하고 **필요한 외부 도구(사내 DB 조회, 이메일 발송, 규정 검색, 시간 확인)를 스케줄링하여 능동적으로 과업을 수행**하는 **ReAct AI Agent** 파이프라인을 구축하는 것.

## 🛠️ 사전 준비 및 환경 세팅 (Prerequisites & Installation)
실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화하고 필요 의존성 패키지를 설치합니다:

```bash
# 1. 저장소 루트로 이동 및 가상환경 생성 (최초 1회)
cd /Users/sangjin/Desktop/workspace/AI_Study
python3 -m venv venv

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 필수 패키지 설치
pip install -r week-03/requirements.txt
```

## 주요 기능
1. **ReAct (Reasoning + Acting) Agent 엔진 (`agent.py`)**:
   - `Thought` (생각) → `Action` (도구 선택 및 인자 전달) → `Observation` (도구 실행 결과 확인) → `Final Answer` (종합 답변) 루프 자율 수행.
   - 무한 루프 방지를 위한 `max_iterations` 보호 장치 탑재.
2. **다양한 외부 도구(Tools) 모음 (`tools.py`)**:
   - `search_policy_docs`: 사내 규정 RAG 검색
   - `query_employee_db`: 직원 부서 및 잔여 연차 DB 조회
   - `send_notification_email`: 이메일/알림 발송
   - `get_current_time`: 현재 시각 조회
3. **환경변수(.env) 기반 API 키 지원 (`.env`)**:
   - `.env` 파일에 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY` 등 주요 키를 사전에 명시하여 용이하게 입력 가능.
   - API 키 없이도 Agent 작동 과정을 투명하게 확인할 수 있는 **Mock Agent LLM** 제공.

## 구성
```
week-03/
├── PLANNING.md          # 3주차 아키텍처 + IT 기획 실수 노트 ★
├── requirements.txt
├── README.md
├── .env.example         # 주요 AI/LLM API 키 템플릿
├── .env                 # 환경변수 파일
└── app/
    ├── main.py          # FastAPI 진입점 (/agent/chat, /agent/tools)
    ├── agent.py         # ReAct Agent 자율 추론 실행 엔진
    ├── tools.py         # 등록된 도구(Tools) 정의 및 실행 래퍼
    ├── llm.py           # .env 자동 로드 & Agent LLM Provider
    ├── rag_helper.py    # 도구용 RAG 검색 도우미
    └── docs/            # 사내 지식베이스
        └── sample_policy.txt
```

## 실행
```bash
# 가상환경 활성화 후 실행
source venv/bin/activate
cd week-03
uvicorn app.main:app --reload
# http://127.0.0.1:8000/docs 에서 POST /agent/chat 및 GET /agent/tools 테스트
```

### 테스트 예시 (Swagger Docs / Curl)
```json
// POST /agent/chat
{
  "question": "김철수 책임의 잔여 연차를 확인하고 이메일로 안내해줘.",
  "provider": "mock"
}
```

## 직접 해보며 배운 것
- **AI Agent의 강력함과 통제의 필요성**: LLM이 스스로 판단해 DB를 조회하고 메일까지 발송하는 워크플로를 구축하면서, agent의 자유도만큼 무한 루프 제한 및 도구 실행 궤적(Trajectory)의 투명성이 핵심 통제 요소임을 확인했다.
- **환경변수(.env) 템플릿화의 이점**: `.env.example`을 통해 다양한 LLM/Agent 관련 키 이름을 사전에 정돈해두니 향후 새로운 LLM 모델을 테스트하거나 연동할 때 직관적이다.

## 다음 주 계획
다음 주(Week 04)에는 하나의 에이전트가 아닌, 여러 에이전트가 각자의 역할을 담당하여 협업하는 **Multi-Agent 시스템 및 상태 머신(LangGraph 스타일)** 구조를 실습할 예정.
