# Week 07 — TypeSafe AI Jev (System One) 기반 정형 의사결정 & 확률적 워크플로 라우팅 아키텍처

## 1. 한 줄 요약
자유 텍스트(Prose)를 생성하는 전통적인 LLM(System Two)의 JSON 파싱 실패, 스키마 환각, 과신(Overconfidence) 한계를 극복하기 위해, **TypeSafe AI의 System One 모델인 `Jev`(`jev-latest`)와 3대 강타입 프리미티브(`Choice`, `Score`, `Noul`)**를 단일 병렬 패스로 평가하고 확률/신뢰도 임계값 기반의 **결정론적 워크플로 라우팅 및 HITL(Human-in-the-Loop) 제어 파이프라인**을 구축한 시스템.

---

## 2. 왜 TypeSafe AI Jev (System One)인가? (실무 엔지니어링 관점)

### (1) 기존 생성형 LLM(System Two)을 M2M 라우팅에 쓸 때의 치명적 한계
- **비정형 토큰 생성 및 파싱 취약성**: GPT-4나 Claude 같은 생성형 모델에 JSON 출력을 지시해도 마크다운 블록(` ```json `), 서두 문장(`Here is the result:`), 또는 프롬프트 인젝션 공격에 의해 정의되지 않은 Enum 키가 생성되어 프로덕션 파이프라인이 중단됩니다.
- **보정되지 않은 언어적 과신(Verbalized Overconfidence)**: LLM에게 "자신의 확신도를 0~1로 적어라"고 프롬프팅하면 실제로는 모호한 복합 문의임에도 `0.95`나 `0.99`를 출력하는 경향이 심해 신뢰도 기반 에스컬레이션(HITL)이 불가능합니다.
- **높은 지연 시간(Latency)**: 단순 분류/라우팅 판단 하나를 위해 수십~수백 개의 텍스트 토큰을 자기회귀(Autoregressive) 방식으로 순차 생성하므로 수백 ms~수 초가 소요됩니다.

### (2) TypeSafe AI Jev (`client.system_one`)의 패러다임 전환
- **No Prose, Pure Typed Decisions**: Jev는 자연어 문장을 생성하지 않습니다. 프로그램 상태(`state`)와 강타입 질문 딕셔너리(`questions`)를 입력받아 **단일 병렬 패스(Single Parallel Pass)**로 모든 질문을 동시에 평가합니다.
- **3대 의사결정 프리미티브 (`Choice`, `Score`, `Noul`)**:
  1. **`Choice` (비서열 다지선다 선택형)**: 최대 255개 옵션 중 최적 옵션을 고르며, 선택된 `choice`, 모든 옵션의 확률 분포(`probabilities`), 그리고 분포의 섀넌 엔트로피 및 마진에 기반한 결정 신뢰도(`confidence`)를 반환합니다.
  2. **`Score` (서열 루브릭 척도형)**: 순서가 있는 2~10단계 기준선(`criteria`) 위에서 각 단계의 확률을 평가하고, 확률 가중 연속 기대 점수($\mathbb{E}[S] = \sum_{i=0}^{N-1} i \cdot P_i$)와 `legend`, `confidence`를 반환합니다.
  3. **`Noul` (이진 참/거짓 확률형)**: 특정 조건이나 진술이 참(Yes)일 확률 `noul`($0.0 \sim 1.0$)을 직접 반환하여 직관적인 가드레일/트리거 분기를 지원합니다.

### (3) System 1 (Jev) + System 2 (Generative LLM) 하이브리드 아키텍처
- **System 1 (Jev)**: 최전방에서 밀리초 단위로 보안 위협 여부(`Noul`), 담당 부서 분류 및 신뢰도(`Choice`), 장애 심각도(`Score`)를 병렬 판정하여 `if / elif / else` 제어 흐름을 결정합니다.
- **System 2 (LLM)**: System 1의 보안 및 신뢰도 게이트를 안전하게 통과한 건에 한해서만 호출되어 고객 안내문이나 SRE 장애 리포트 등 자연어 텍스트를 합성합니다.

---

## 3. 시스템 아키텍처 및 파이프라인 흐름

```
[프로그램 상태 (State: 고객 티켓 / 웹훅 페이로드 / 장애 이벤트 JSON)]
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│     TypeSafe AI Jev — client.system_one(model="jev-latest")   │
│                [Single Parallel Pass Evaluation]              │
├───────────────────┬─────────────────────┬─────────────────────┤
│  Choice           │  Score              │  Noul (x2)          │
│  - department     │  - severity (0~3)   │  - refund_requested │
│  - probabilities  │  - expected score   │  - security_risk    │
│  - confidence     │  - legend & probs   │  - noul (0.0 ~ 1.0) │
└─────────┬─────────┴──────────┬──────────┴──────────┬──────────┘
          └────────────────────┼─────────────────────┘
                               ▼
       ┌───────────────────────────────────────────────┐
       │   Deterministic Probability Gate Controller   │
       └───────────────────────┬───────────────────────┘
                               │
     ┌─────────────────────────┼─────────────────────────┐
     ▼                         ▼                         ▼
[Gate 1: Security]     [Gate 2: Confidence]     [Gate 3 & 4: Auto Action]
security.noul >= 0.65  dept.confidence < 0.55   High Confidence & Safe
     │                         │                         │
     ▼                         ▼                         ▼
🚨 즉시 격리 & 차단     🧑‍💻 HITL 수동 검토 큐      ⚡ 무인 자동화 파이프라인
(System 2 호출 차단)    (전체 확률 분포표 첨부)   (자동 환불 / SRE Pager 가동)
```

---

## 4. 실행 및 테스트 방법

### (1) 서버 실행
```bash
# 1. 저장소 루트에서 가상환경 활성화
cd /Users/sangjin/Desktop/workspace/AI_Study
source venv/bin/activate

# 2. 7주차 폴더로 이동 후 실행
cd week-07
uvicorn app.main:app --reload
```

### (2) 브라우저 접속 (대화형 학습 포털)
- 접속 URL: `http://127.0.0.1:8000`
- 탭 1: ⚡ **Jev 3대 프리미티브 병렬 평가기** (`Choice`, `Score`, `Noul` 확률 분포 및 신뢰도 실시간 시각화)
- 탭 2: 🧭 **확률 게이트 라우팅 & HITL 시뮬레이터** (4대 임계값 슬라이더 조작을 통한 실시간 `if/else` 분기 실험)
- 탭 3: ⚖️ **System 1 (Jev) vs System 2 (LLM) 비교 실험실** (타입 안전성, 프롬프트 인젝션 방어력, 지연 시간 비교)
- 탭 4: 📘 **다시 보고 배우는 학습 허브** (표준 SDK 코드 패턴, 10가지 실수 노트 및 1~7주차 로드맵)

---

## 5. 만들어보며 겪은 10가지 실수 노트 (중요 트러블슈팅)

| # | 문제 현상 | 왜 발생했나? (원인) | 이렇게 해결함 (해결책) |
|---|-----------|---------------------|------------------------|
| 1 | **생성형 LLM으로 라우팅 구현 시 `json.loads` 파싱 장애** | LLM이 JSON 앞뒤에 설명 문구를 붙이거나 프롬프트 인젝션으로 스키마 외 키를 생성함 | 자유 텍스트를 생성하지 않는 System One 모델(TypeSafe AI Jev)의 `Choice`, `Score`, `Noul` 강타입 프리미티브로 전환 |
| 2 | **복합 문의(요금제+기술+보안)를 잘못된 부서로 자동 배정** | 최고 확률 1순위(`choice`) 값만 보고 `confidence`(결정 신뢰도)를 확인하지 않아 모호한 티켓도 강제 라우팅함 | `department.confidence < 0.55`일 때는 자동 배정을 멈추고 전체 확률 분포표를 첨부해 HITL(사람 검토 큐)로 에스컬레이션 |
| 3 | **순서가 있는 심각도(Severity)를 `Choice`로 잘못 모델링** | `Choice`는 순서가 없는 범주형이어서 1단계와 3단계에 확률이 나뉠 때 중간 기대값을 계산할 수 없음 | 서열 척도 전용 프리미티브인 `Score`를 사용하여 확률 가중 연속 기대 점수($E[S] = \sum i \cdot P_i$)로 정밀 평가 |
| 4 | **Yes/No 판별을 `Choice(["yes", "no"])`로 불필요하게 중복 정의** | 단순 참/거짓 조건 검증에 다지선다 구조체를 쓰면 코드 가독성과 임계값 직관성이 떨어짐 | 이진 확률 전용 프리미티브인 `Noul`을 사용하여 `response.answers["refund"].noul >= 0.70` 형태로 간결화 |
| 5 | **여러 질문을 루프(`for`)로 4번 나눠 호출하여 Latency 4배 증가** | `department`, `severity`, `refund`, `security`를 각각 별도 API 요청으로 직렬 호출함 | `client.system_one(state=..., questions={...})`의 `questions` 딕셔너리에 묶어 **단일 병렬 패스(Single Parallel Pass)**로 1회 호출 |
| 6 | **프롬프트 인젝션 공격이 포함된 티켓을 System 2 LLM에 바로 전달** | 가드레일 없이 생성형 LLM이 사용자 원문을 먼저 요약/답변하게 하여 시스템 프롬프트 탈취 위험 노출 | System 1(Jev)의 `security_risk` `Noul` 게이트를 최상단(Gate 1)에 배치하여 임계값 초과 시 System 2 호출을 원천 차단 |
| 7 | **`Score` 루브릭 기준(`criteria`)의 순서를 뒤섞어 작성** | 루브릭 리스트에 `[높음, 낮음, 중간]`처럼 서열 순서를 지키지 않아 가중 평균 점수의 의미가 왜곡됨 | 반드시 가장 낮은 단계(0점)부터 가장 높은 단계(N-1점)까지 단조 증가 순서로 `criteria`를 정렬 |
| 8 | **`Choice` 옵션 이름만 간략히 적고 판단 기준(`criteria` 설명) 누락** | 옵션 키(`["t1", "t2"]`)만 전달하면 모델이 도메인 맥락을 정확히 구분하지 못해 확률이 분산됨 | `criteria={"billing": "결제 오류, 중복 청구 및 환불...", "technical_sre": "..."}`처럼 명확한 기준 설명을 함께 제공 |
| 9 | **확률 분포 반올림 오차로 인해 옵션 확률 합계가 `0.9999`가 됨** | 부동소수점 Softmax 계산 후 소수점 4자리 반올림 시 미세 오차 발생 | 최대 확률 항목에 `1.0 - sum(probs)` 잔차를 보정하여 확률 합계가 정확히 `1.0`을 만족하도록 정규화 |
| 10 | **`TYPESAFE_API_KEY` 미보유 환경에서 실습 및 테스트 불가** | 외부 클라우드 SDK에만 의존하면 오프라인이나 키 미발급 환경에서 파이프라인 검증이 불가능함 | Softmax 확률 분포, 섀넌 엔트로피 기반 Confidence, 루브릭 기대값 수식을 내장한 로컬 확률 추론 엔진을 함께 구현 |

---

## 6. 나중에 다시 보고 배울 핵심 체크포인트 (Re-learning Checkpoints)

1. **`Score` 프리미티브의 연속 기대 점수 수식**:
   $$\mathbb{E}[Score] = \sum_{i=0}^{N-1} i \cdot P(\text{level}_i)$$
   - 단순 정수 분류(`0, 1, 2, 3`)가 아니라, 2단계($P=0.4$)와 3단계($P=0.6$) 사이에 걸친 미묘한 심각도를 `2.60`이라는 연속 실수로 포착하여 정교한 임계값(`>= 1.80`) 설정을 가능하게 합니다.
2. **`Choice` 신뢰도(Confidence)와 엔트로피**:
   $$\text{Confidence}(P) = w_1 \left(1 - \frac{-\sum_{k=1}^{K} P_k \log P_k}{\log K}\right) + w_2 (P_{(1)} - P_{(2)})$$
   - 1순위 확률만 높은지, 아니면 1순위와 2순위가 비등하게 경합 중인지(모호한 상태)를 정확히 구분하여 자동화 사고를 예방합니다.
3. **System 1 + System 2 역할 분담 원칙**:
   - **라우팅, 분류, 우선순위 채점, 가드레일 판정** $\to$ **System 1 (TypeSafe AI Jev)**
   - **최종 자연어 안내문 작성, 코드 생성, 창의적 요약** $\to$ **System 2 (Generative LLM)**

