---
title: AI Study 전체 아키텍처 진화 개요
category: 아키텍처
tags: [RAG, Agent, Multi-Agent, Hybrid-RAG, System-One]
updated: 2026-11-18
okf_version: "0.2"
summary: 1주차 최소 RAG 챗봇부터 7주차 TypeSafe AI Jev 정형 의사결정 시스템까지 AI 아키텍처의 단계별 진화 과정을 정리한 문서입니다.
infobox:
  범위: Week 01 ~ Week 07
  핵심 스택: FastAPI, ChromaDB, BM25, Jev
  관련 문서: hybrid-rag, system-one-jev
---

# AI Study 전체 아키텍처 진화 개요

본 저장소는 매주 하나의 실무형 AI/아키텍처 과제를 직접 구축하며 **검색(Retrieval) → 추론(Reasoning) → 협업(Orchestration) → 평가(Evaluation) → 정형 제어(System One)**로 확장되는 계보를 다룹니다.

---

## 주차별 아키텍처 계보

| 주차 | 핵심 주제 | 주요 해결 과제 |
|:---:|:---|:---|
| **Week 01** | 최소 RAG 챗봇 | ChromaDB + SentenceTransformers 기반 임베딩 및 코사인 유사도 검색 |
| **Week 02** | RAG + LLM & 메모리 | 세션 컨텍스트 유지 및 입력 가드레일 적용 |
| **Week 03** | AI Agent & Function Calling | ReAct 패턴 기반 사내 DB/이메일/RAG 도구 자율 호출 |
| **Week 04** | Multi-Agent 협업 | Planner-Researcher-Reviewer 역할 분담 및 상태 머신 |
| **Week 05** | Evaluator-Optimizer | LLM-as-a-Judge 4대 루브릭 채점 및 Latency Observability |
| **Week 06** | [[architecture/hybrid-rag\|Advanced Hybrid RAG]] | BM25 + Dense Vector + RRF + Cross-Encoder Reranker + Ragas 3대 지표 |
| **Week 07** | [[architecture/system-one-jev\|TypeSafe AI Jev]] | 자유 텍스트 없는 강타입 병렬 의사결정(`Choice`, `Score`, `Noul`) 및 HITL 라우팅 |

---

## 다음 단계: OpenWiki 기반 지식 그래프
코드베이스가 커질수록 에이전트와 개발자 모두가 아키텍처 맥락을 잃지 않도록 [[guides/openwiki-workflow|LangChain OpenWiki]]를 통해 위키 문서를 지속 관리하고, [[guides/ec2-deployment|AWS EC2]]에 위키피디아 포털로 상시 배포합니다.

