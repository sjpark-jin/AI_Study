# Week 04 — Multi-Agent 협업 및 워크플로 상태 관리

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 4주차 주제는 **Multi-Agent 시스템**.

## 이번 주에 하고 싶었던 것
에이전트 하나에게 모든 작업을 맡기지 않고, **기획(Planner) → 조사(Researcher) → 검수(Reviewer)** 로 역할을 나누어 순차적으로 일하고 검증하는 **멀티 에이전트 워크플로**를 만드는 것.

## 🛠️ 사전 준비 및 환경 세팅
실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화합니다:

```bash
# 1. 저장소 루트로 이동
cd /Users/sangjin/Desktop/workspace/AI_Study

# 2. 가상환경 활성화
source venv/bin/activate

# 3. 4주차 폴더로 이동 및 실행
cd week-04
uvicorn app.main:app --reload
# 접속: http://127.0.0.1:8000/docs
```

## 주요 기능
1. **역할 분담 에이전트 (`agents.py`)**:
   - `PlannerAgent`: 질문을 보고 필요한 작업 단계(계획) 수립.
   - `ResearcherAgent`: 계획대로 RAG 지식베이스나 사내 DB를 조회해 근거 데이터 수집.
   - `ReviewerAgent`: 수집된 데이터를 확인하고 누락이나 오류가 없는지 최종 검수.
2. **상태 워크플로 오케스트레이터 (`orchestrator.py`)**:
   - `START → PLAN → RESEARCH → REVIEW → FINISH` 로 이어지는 상태 머신(State Machine)을 구동.
   - 검수 실패 시 `RESEARCH` 단계로 돌려보내 다시 조사를 요청하며, 무한 루프 방지를 위해 최대 2회까지만 재시도.

## 구성
```
week-04/
├── PLANNING.md          # 4주차 아키텍처 및 실수 노트 ★
├── requirements.txt
├── .env.example         # 환경변수 템플릿
├── .env                 # 환경변수 파일
├── README.md
└── app/
    ├── main.py          # FastAPI 진입점 (/multiagent/run, /multiagent/graph)
    ├── orchestrator.py  # 상태 머신 및 흐름 제어
    ├── agents.py        # Planner, Researcher, Reviewer 에이전트
    ├── tools.py         # 3주차 도구 및 실행 래퍼
    ├── rag_helper.py    # RAG 검색 도우미
    └── docs/
        └── sample_policy.txt
```

## 실행 및 테스트 예시

### API 테스트 (Swagger Docs / Curl)
```json
// POST /multiagent/run
{
  "user_request": "김철수 책임의 연차를 확인하고 메일로 보내줘."
}
```

### 응답 결과 예시
```json
{
  "user_request": "김철수 책임의 연차를 확인하고 메일로 보내줘.",
  "final_answer": "멀티 에이전트 협업 검수 완료 답변...",
  "status": "APPROVED",
  "plan": [
    "1. 사내 DB에서 해당 직원의 인적사항 및 잔여 연차 조회",
    "3. 조회 결과를 담당자에게 이메일로 발송"
  ],
  "findings_count": 2,
  "workflow_history": [ ... ],
  "latency_ms": 12.5
}
```

## 직접 해보며 배운 것
- **혼자 다 하게 하는 것보다 역할을 쪼개는 게 확실히 안정적이다**: 단일 에이전트일 때는 지시사항을 빼먹는 일이 흔했는데, Planner가 쪼개주고 Reviewer가 감시하니 빠뜨리는 조건이 크게 줄었다.
- **순서도(State Flow)가 없으면 제어가 안 된다**: 에이전트끼리 대화만 하게 두면 산으로 가기 때문에, 코드로 정확한 상태 전이 경로를 정해주는 것이 핵심이었다.
