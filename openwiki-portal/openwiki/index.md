---
title: OpenWiki 지식 백과 (Main Page)
category: 대문
tags: [OpenWiki, LangChain, OKF, Knowledge-Graph, AI-Study]
updated: 2026-11-18
okf_version: "0.2"
summary: LangChain OpenWiki CLI가 GitHub 저장소 내에 생성·유지보수하는 마크다운(.md) 기반 위키피디아 포털의 루트 인덱스 문서입니다.
infobox:
  프로젝트: OpenWiki Portal
  기반 기술: LangChain OpenWiki (OKF v0.2)
  웹 엔진: FastAPI + Vanilla SPA
  배포 환경: AWS EC2 (Nginx + Systemd)
  문서 형식: Markdown + YAML Front Matter
---

# OpenWiki 지식 백과에 오신 것을 환영합니다

**OpenWiki**는 LangChain(`langchain-ai/openwiki`)이 제안한 오픈소스 CLI 및 에이전트 프레임워크로, GitHub 저장소의 코드 변경분(`git diff`)을 추적하여 AI 에이전트와 사람이 모두 탐색하기 좋은 **구조화된 마크다운 위키(`openwiki/`)**를 자동으로 생성하고 최신 상태로 유지합니다.

이 웹 포털은 GitHub 저장소 내 `openwiki/` 폴더에 쌓인 `.md` 파일들을 실시간으로 파싱하여 **위키피디아(Wikipedia) 스타일의 백과사전 홈페이지**로 제공합니다.

---

## 주요 문서 디렉터리 (Index)

### 1. 아키텍처 & AI 엔지니어링
- [[architecture/overview|AI Study 전체 아키텍처 진화 개요]] — Week 01(최소 RAG)부터 Week 07(TypeSafe AI Jev)까지의 시스템 발전사
- [[architecture/hybrid-rag|Advanced Hybrid RAG 파이프라인]] — BM25 키워드 검색, Dense Vector, RRF 및 Cross-Encoder Reranker
- [[architecture/system-one-jev|TypeSafe AI Jev (System One) 정형 의사결정]] — `Choice`, `Score`, `Noul` 기반 확률적 워크플로 라우팅

### 2. 운영 & 배포 가이드
- [[guides/openwiki-workflow|LangChain OpenWiki CLI & GitHub 자동 동기화 가이드]] — `openwiki --init`, `openwiki --update` 및 CI/CD 연동법
- [[guides/ec2-deployment|AWS EC2 프로덕션 배포 가이드]] — Ubuntu EC2 인스턴스에 Nginx + Systemd로 위키 포털 올리기

### 3. 변경 이력 (Changelog)
- [[logs|OpenWiki 변경 로그 (logs.md)]] — Git 커밋 기반 위키 문서 자동 갱신 이력

---

## 동작 원리 요약

1. **GitHub 저장소 문서화**: 로컬 또는 GitHub Actions에서 `openwiki --init` / `openwiki --update`를 실행하면 `openwiki/` 폴더에 `index.md`, `logs.md`와 주제별 `.md` 파일이 생성됩니다.
2. **그래프 & 백링크 파싱**: 백엔드(`wiki_loader.py`)가 모든 `.md` 파일의 YAML Front Matter, 목차(TOC), 내부 링크(`[[...]]`, `[...](...)`), 역참조 백링크(Backlinks)를 자동 인덱싱합니다.
3. **위키피디아 웹 제공**: `index.html`이 인포박스(Infobox), 목차, 본문, 백링크, 전문 검색(Full-Text Search)을 위키피디아 UI로 렌더링합니다.

