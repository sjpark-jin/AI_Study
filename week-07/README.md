# Week 07 — TypeSafe AI Jev (System One) 기반 정형 의사결정 & 확률적 워크플로 라우팅

주 1회 AI/아키텍처를 하나씩 직접 세팅해보며 정리하는 학습 기록. 7주차 주제는 **TypeSafe AI의 System One 모델인 `Jev`를 활용한 강타입(Type-Safe) 병렬 의사결정 및 확률 임계값 기반 워크플로 제어 아키텍처**.

## 이번 주에 하고 싶었던 것
일반적인 생성형 LLM(System Two)으로 티켓 라우팅이나 가드레일을 구현할 때 겪는 고질적인 문제(JSON 파싱 에러, 프롬프트 인젝션에 의한 스키마 오염, 보정되지 않은 과신 확률, 느린 토큰 생성 지연)를 해결하기 위해, **자유 텍스트를 생성하지 않는 TypeSafe AI `Jev` 모델(`client.system_one`)과 3대 강타입 프리미티브(`Choice`, `Score`, `Noul`)**를 도입하는 것.
그리고 Jev가 단일 병렬 패스로 반환한 확률 분포(`probabilities`), 기대 점수(`score`), 신뢰도(`confidence`), 참 확률(`noul`)을 바탕으로 **보안 서킷 브레이커, 무인 자동 환불/SRE 호출, 그리고 신뢰도 미달 시 Human-in-the-Loop(HITL) 수동 큐로 이관하는 엔터프라이즈 라우팅 포털**을 구축하는 것.

---

## 🛠️ 사전 준비 및 환경 세팅

실행 전 저장소 루트에서 Python 가상환경(`venv`)을 활성화합니다:

```bash
# 1. 저장소 루트로 이동
cd /Users/sangjin/Desktop/workspace/AI_Study

# 2. 가상환경 활성화 (macOS / Linux)
source venv/bin/activate

# 3. (선택) 실제 TypeSafe AI 클라우드 API 연동 시 SDK 설치
# pip install typesafe-sdk

# 4. 7주차 폴더로 이동 및 서버 실행
cd week-07
uvicorn app.main:app --reload

# 5. 브라우저 접속
# 대화형 학습 웹 UI: http://127.0.0.1:8000
# Swagger API 문서: http://127.0.0.1:8000/docs
```

---

## 주요 기능

1. **TypeSafe AI Jev 3대 프리미티브 병렬 평가 엔진 (`jev_engine.py`)**:
   - **`Choice` (선택형 분류)**: 담당 부서(`billing`, `technical_sre`, `security_cert`, `account_sales`)별 확률 분포(`probabilities`)와 엔트로피 기반 결정 신뢰도(`confidence`) 산출.
   - **`Score` (서열 루브릭 척도)**: 4단계 심각도 루브릭(`criteria`)에 대한 확률 가중 연속 기대 점수($\mathbb{E}[S] = \sum i \cdot P_i$) 및 `legend` 반환.
   - **`Noul` (이진 참/거짓 확률)**: 환불 요청 여부(`refund_requested`) 및 보안 위협/프롬프트 인젝션 포함 여부(`security_risk`)를 $0.0 \sim 1.0$ 확률로 즉시 판정.
   - 실제 `typesafe-sdk` 연동과 오프라인 보정 확률 시뮬레이터를 모두 지원하여 API 키 없이도 즉시 실습 가능.

2. **확률 임계값 기반 4단계 결정론적 게이트 라우터 (`workflow_router.py`)**:
   - **Gate 1 (Security Circuit Breaker)**: `security_risk.noul >= 0.65` 시 System 2 LLM 호출을 즉시 차단하고 보안 격리.
   - **Gate 2 (Confidence HITL Gate)**: `department.confidence < 0.55` (복합/모호 문의) 시 잘못된 자동 배정을 막고 전체 확률 분포표를 첨부해 사람 검토 큐(HITL)로 이관.
   - **Gate 3 (Critical SRE Pager)**: `severity.score >= 1.80` 및 `technical_sre` 판정 시 PagerDuty P1 긴급 런북 가동.
   - **Gate 4 (Automated Refund Pipeline)**: `billing` 및 `refund_requested.noul >= 0.70` 충족 시 무인 결제 취소/환불 파이프라인 실행.

3. **System 1 (Jev) vs System 2 (Generative LLM JSON) 비교 실험실 (`benchmark.py`, `index.html`)**:
   - 동일한 입력 상태(State)에 대해 Jev의 단일 병렬 패스 평가와 생성형 LLM JSON 프롬프팅의 스키마 안전성, 프롬프트 인젝션 내성, 지연 시간을 실시간 대조.

---

## 구성

```
week-07/
├── PLANNING.md          # 7주차 아키텍처, 3대 프리미티브 수식, 10가지 실수 노트 ★
├── requirements.txt     # 의존성 패키지 명세
├── .env.example         # 환경변수 템플릿 (TYPESAFE_API_KEY 및 확률 임계값)
├── .env                 # 로컬 환경변수 파일
├── README.md            # 주차 소개 및 실행 가이드
└── app/
    ├── main.py          # FastAPI 진입점 및 웹 UI 라우트
    ├── jev_engine.py    # TypeSafe AI Jev SDK 래퍼 & Choice/Score/Noul 확률 추론 엔진
    ├── workflow_router.py # 확률 게이트 라우팅, HITL 분기 & System 1+2 하이브리드 제어기
    ├── benchmark.py     # System 1 (Jev) vs System 2 (LLM JSON) 비교 실험 모듈
    ├── llm.py           # System 2 자연어 리포트 합성용 Mock 및 OpenAI 프로바이더
    ├── static/
    │   └── index.html   # 다크모드 대화형 학습 대시보드 (4개 탭)
    └── docs/
        └── sample_states.json # 결제 환불, SRE 장애, 보안 인젝션, 모호한 복합 문의 샘플 State
```

---

## 실행 및 테스트 예시

### 1. Jev `system_one` 병렬 평가 (`POST /jev/system-one`)
```json
// 요청 (Request)
{
  "model": "jev-latest",
  "state": {
    "ticket_id": "TCK-2026-8901",
    "subject": "주문번호 ORD-7741 중복 결제 즉시 환불 요청",
    "message": "프로 플랜 갱신 중 $1,200가 두 번 결제되었습니다. 즉시 환불 부탁드립니다."
  }
}

// 응답 (Response 요약)
{
  "model": "jev-latest",
  "parallel_questions_count": 4,
  "answers": {
    "department": {
      "primitive_type": "Choice",
      "choice": "billing",
      "probabilities": { "billing": 0.9412, "account_sales": 0.0315, "technical_sre": 0.0152, "security_cert": 0.0121 },
      "confidence": 0.8924
    },
    "severity": {
      "primitive_type": "Score",
      "score": 2.0841,
      "confidence": 0.7815
    },
    "refund_requested": {
      "primitive_type": "Noul",
      "noul": 0.934,
      "verdict": true
    },
    "security_risk": {
      "primitive_type": "Noul",
      "noul": 0.1419,
      "verdict": false
    }
  }
}
```

### 2. 확률 임계값 기반 워크플로 라우팅 (`POST /workflow/route`)
```json
// 요청 (Request)
{
  "state": "다음 달에 플랜을 바꿀까 고민 중인데 웹훅 스펙도 달라지나요? 보안 감사 서류 양식도 같이 문의드립니다.",
  "thresholds": {
    "confidence_threshold": 0.55,
    "urgency_score_threshold": 1.8,
    "security_noul_threshold": 0.65,
    "refund_noul_threshold": 0.7
  }
}

// 응답 (Response 요약)
{
  "route_code": "HITL_HUMAN_QUEUE",
  "route_title": "🧑‍💻 Human-in-the-Loop 수동 검토 이관 (신뢰도 미달 방어)",
  "automation_mode": "HITL_ESCALATED",
  "assigned_team": "시니어 트리아지 매니저 큐 (확률 분포표 첨부)",
  "triggered_rule": "answers['department'].confidence (0.31) < 0.55"
}
```

---

## 직접 해보며 배운 것

- **머신-투-머신 제어 흐름에 생성형 텍스트(Prose)는 독이다**: 소프트웨어 코드가 필요한 것은 화려한 문장이 아니라 **타입이 보장된 선택지(`Choice`), 정량 척도(`Score`), 참/거짓 확률(`Noul`)**이다. Jev처럼 처음부터 생성을 배제하고 확률 분포만 반환하는 System One 모델을 쓰면 파싱 예외와 스키마 환각이 완전히 사라진다.
- **최고 확률 선택값(`choice`)만큼 중요한 것이 결정 신뢰도(`confidence`)다**: 4개 부서 확률이 `[0.32, 0.28, 0.22, 0.18]`일 때 무조건 1위(0.32) 부서로 자동 배정하면 오배정 사고가 난다. `confidence` 임계값 게이트를 걸어 애매한 건만 사람(HITL)에게 넘기는 것이 실무 AI 자동화의 핵심 안전장치다.
- **System 1(Jev)과 System 2(LLM)를 결합하면 속도와 안전성을 모두 잡는다**: Jev를 앞단 게이트키퍼로 두면 프롬프트 인젝션이나 불확실한 요청이 무거운 생성형 LLM까지 도달하지 않아 비용과 보안 리스크를 동시에 줄일 수 있다.

