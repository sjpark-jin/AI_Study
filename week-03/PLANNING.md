# Week 03 — AI Agent & Function Calling (도구 사용하는 AI 에이전트 구축)

## 1. 한 줄 요약
1~2주차의 단순 질의응답(RAG) 수준을 넘어, LLM이 사용자 질문을 분석하여 **필요한 외부 도구(사내 DB 조회, 이메일 발송, 지식베이스 검색, 시각 조회)를 스스로 판단해 선택 및 연동 실행**하는 **ReAct (Reasoning + Acting) AI Agent**를 구축했다.

## 2. 왜 이 구성인가 (IT기획 관점)
- **단순 챗봇 vs AI Agent의 차이**:
  - 기존 LLM/RAG: 텍스트를 읽고 답변만 생성 (수동적).
  - **AI Agent**: 목표 달성을 위해 사내 API를 호출하거나 DB를 수정/조회하는 등의 **행동(Action)을 직접 실행** (능동적).
- **Function Calling (도구 호출)의 핵심 가치**:
  - LLM에게 실시간 데이터베이스 조회권이나 업무 자동화 기능(이메일 발송, 결재 승인 등)을 안전한 파라미터 스키마 형태로 부여할 수 있다.
- **Agent의 통제와 가드레일**:
  - Agent가 자율적으로 판단하도록 두면 무한 루프에 빠지거나, 불필요한 API를 수십 번 호출해 **비용 폭발 및 데이터 오용 리스크**가 발생한다.
  - 이를 방지하기 위해 **최대 실행 횟수(max_iterations) 제한, 도구별 권한 분리, 실행 과정(Trajectory/Thought)의 실시간 모니터링**이 필수적이다.

## 3. 아키텍처
```
[사용자 요청] ("김철수 책임 연차 조회 후 메일 보내줘")
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│              ReAct Agent Execution Engine                │
│                                                          │
│  [Step 1] Thought: "직원 DB에서 김철수 잔여 연차 조회가 필요함"│
│           Action: query_employee_db(employee_name="김철수")│
│           Observation: "사번: E1001, 잔여 연차: 8.5일"     │
│                                                          │
│  [Step 2] Thought: "조회 성공. 이메일 알림 발송 도구 실행"   │
│           Action: send_notification_email(...)           │
│           Observation: "[발송 성공] 메일 송신 완료"          │
│                                                          │
│  [Step 3] Thought: "모든 작업 완수. 최종 답변 구성"           │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼
[FastAPI /agent/chat 응답] ──► JSON (final_answer, trajectory, total_steps)
```

## 4. 실행 방법
```bash
cd week-03
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# 브라우저: http://127.0.0.1:8000/docs 에서 POST /agent/chat 테스트
```

## 5. 세팅하며 직접 밟은 실수 정리 (중요)

| # | 흔한 실수 | 증상 | 대응 |
|---|-----------|------|------|
| 1 | **Agent 무한 루프(Runaway Call) 방치** | LLM이 목적을 달성하지 못하고 도구를 무한 반복 실행하여 서버 마비 및 API 비용 폭발 | Agent 엔진에 `max_iterations = 5` 제한 및 강제 루프 중단 예외 처리 적용 |
| 2 | **도구(Tool) 파라미터 타입 불일치 및 미검증** | LLM이 전달한 인자(kwargs)가 숫자형이어야 하는데 문자열로 넘겨 도구 함수 Crash | Pydantic / 표준 Python 파라미터 타입 검증 및 `try-except` 처리로 도구 에러 가호성 확보 |
| 3 | **Agent의 내부 추론 과정(Thought)을 은폐** | 최종 답변만 출력되어 Agent가 왜 그런 도구를 썼는지 또는 왜 잘못된 행동을 했는지 디버깅 불가 | 응답에 `trajectory` (Step별 Thought, Action, Observation)를 투명하게 포함해 추적 지원 |
| 4 | **쓰기/삭제 권한 도구를 검증 없이 Agent에 부여** | Agent 환각이나 오판으로 DB 데이터 훼손 또는 오발송 사고 발생 | 단순 조회(Read) 도구와 상태 변경(Write) 도구의 권한을 구분하고, 중요한 액션은 승인 단계 고려 |
| 5 | **API 키가 없으면 Agent 전체 개발/테스트 불가** | 외부 LLM API 연결 장애 시 전체 프로젝트 개발 정지 | ReAct 생각(Thought)과 도구 호출(Action)을 완벽 시뮬레이션하는 **Mock Agent Provider** 기본 탑재 |
| 6 | **도구 설명(Description)을 대충 작성** | LLM이 어느 상황에 어떤 도구를 써야 하는지 몰라 엉뚱한 도구를 호출하거나 환각 발생 | 도구별 `description`과 `parameters` 스키마를 유즈케이스 명시형으로 정교하게 작성 |
| 7 | **환경변수(.env) 미적용으로 API 키 하드코딩 유출** | GitHub에 소스코드를 올렸다가 API 키 유출 사고 발생 | `.env.example` 및 `.env` 파일 지원과 `.gitignore` 등록으로 보안 키 완벽 격리 |
| 8 | **단일 질의에 여러 도구를 순차 실행할 때 이전 결과를 잊음** | 1단계 도구 결과(Observation)가 2단계 LLM 입력에 누적되지 않고 누락됨 | ReAct 궤적(Trajectory) 전체를 다음 단계 LLM 프롬프트 입력으로 지속 누적 전송 |
| 9 | **외부 도구 실행 타임아웃 미비** | 특정 외부 API나 DB 응답 지연 시 Agent 전체 요청이 멈춤 (Hanging) | 도구 실행부 타임아웃 및 에러 발생 시 에러 메세지를 Observation으로 전환해 에이전트 자가 회복 유도 |
| 10 | **사용자 질문 의도와 무관하게 도구를 습관적으로 남발** | "안녕?" 같은 인사에도 굳이 DB 조회를 실행해 불필요한 지연 발생 | LLM 단계에서 도구 호출이 불필요하면 즉시 `final_answer`를 반환하도록 추론 분기 적용 |

## 6. 다음 주 확장 후보 (Week 04)
- **Multi-Agent 시스템**: 기획 에이전트, 개발 에이전트, 검수 에이전트가 역할을 나누어 상호 대화하는 협업 체계
- **LangGraph 스타일 State Machine**: 그래프 기반으로 에이전트 작업 상태 및 에러 복구 경로 시각화
