---
title: TypeSafe AI Jev (System One) 정형 의사결정
category: 아키텍처
tags: [TypeSafe-AI, Jev, System-One, Choice, Score, Noul, HITL]
updated: 2026-11-18
okf_version: "0.2"
summary: 자유 텍스트 생성을 배제하고 Choice, Score, Noul 강타입 프리미티브로 확률 분포와 신뢰도를 즉시 반환하는 System One 모델 아키텍처입니다.
infobox:
  모델: TypeSafe AI Jev (jev-latest)
  패러다임: System One (Non-Generative)
  프리미티브: Choice, Score, Noul
  안전장치: Security Gate & HITL Escalation
---

# TypeSafe AI Jev (System One) 정형 의사결정

생성형 LLM(System Two)에 JSON 포맷 출력을 지시해 소프트웨어 라우팅을 구현하면 마크다운 혼입, 프롬프트 인젝션에 의한 스키마 파괴, 그리고 모호한 질문에도 `0.95` 이상의 확신도를 출력하는 언어적 과신(Overconfidence) 문제가 발생합니다.

---

## 3대 강타입 질문 프리미티브 (`client.system_one`)

- **`Choice`**: 비서열 다지선다 옵션 중 하나를 선택하고, 전체 옵션 확률 분포(`probabilities`)와 엔트로피 기반 신뢰도(`confidence`)를 반환합니다.
- **`Score`**: 순서가 있는 루브릭(Rubric) 단계별 확률을 계산해 연속 기대 점수($\mathbb{E}[S] = \sum i \cdot P_i$)를 산출합니다.
- **`Noul`**: 특정 조건(예: 환불 요청 여부, 보안 위협 여부)이 참일 확률을 `0.0 ~ 1.0`으로 반환합니다.

---

## 확률 게이트 기반 제어 흐름
- **보안 서킷 브레이커**: `security_risk.noul >= 0.65`일 경우 System Two(생성형 LLM) 호출 자체를 원천 차단합니다.
- **HITL 에스컬레이션**: `department.confidence < 0.55`인 복합/모호 티켓은 자동 배정하지 않고 확률 분포표와 함께 사람 검토 큐로 이관합니다.

자세한 전체 계보는 [[architecture/overview|AI Study 전체 아키텍처 진화 개요]]를 확인하세요.

