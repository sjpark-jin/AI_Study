---
title: LangChain OpenWiki CLI & GitHub 자동 동기화 가이드
category: 가이드
tags: [LangChain, OpenWiki, GitHub, CLI, OKF, CI/CD]
updated: 2026-11-18
okf_version: "0.2"
summary: langchain-ai/openwiki CLI를 사용해 GitHub 저장소에 .md 위키 폴더를 생성하고, 본 웹 포털과 실시간 동기화하는 방법을 설명합니다.
infobox:
  패키지: openwiki (npm)
  요구 런타임: Node.js 22.22+ & Git
  표준 포맷: Open Knowledge Format (OKF)
---

# LangChain OpenWiki CLI & GitHub 자동 동기화 가이드

**OpenWiki**(`langchain-ai/openwiki`)는 코드베이스를 분석해 `openwiki/` 폴더 내에 마크다운 위키를 자동 생성하고, 이후 코드 변경분(`git diff`)만 추적해 문서를 최신 상태로 유지하는 CLI 도구입니다.

---

## 1. OpenWiki CLI 설치 및 초기화

```bash
# Node.js 22.22+ 환경에서 전역 설치
npm install -g openwiki

# GitHub 저장소 루트에서 위키 초기화 (openwiki/ 폴더 및 index.md 생성)
openwiki --init

# 이후 코드 변경 시 증분 업데이트
openwiki --update
```

OpenWiki가 생성하는 `openwiki/` 폴더에는 다음 구조가 포함됩니다:
- `index.md`: 전체 위키 개념을 연결하는 루트 인덱스
- `logs.md`: 변경 이력 및 diff 감사 로그 ([[logs|logs.md 보기]])
- 주제별 `.md` 파일들: YAML Front Matter와 상호 링크로 연결된 문서

---

## 2. 본 웹 포털과 GitHub 저장소 연동하기

이 포털은 **로컬 `openwiki/` 폴더**뿐 아니라 **원격 GitHub 저장소의 특정 폴더**에서 `.md` 파일을 직접 읽어와 위키피디아 형태로 렌더링할 수 있습니다.

1. 웹 포털 상단 또는 사이드바의 **`GitHub 동기화`** 버튼을 클릭합니다.
2. `owner/repo` (예: `langchain-ai/openwiki` 또는 본인 저장소), 브랜치(`main`), 폴더 경로(`openwiki`)를 입력합니다.
3. 서버가 GitHub Contents API를 통해 해당 폴더의 모든 `.md` 파일을 내려받아 즉시 위키 그래프와 백링크를 재구성합니다.

---

## 3. EC2 서버 자동 최신화 (GitHub Actions / Webhook)
[[guides/ec2-deployment|AWS EC2 프로덕션 배포 가이드]]에 따라 EC2에 서버를 올린 뒤, GitHub Actions에서 `openwiki --update`로 문서를 커밋하고 EC2의 `POST /api/wiki/sync` 엔드포인트를 호출하면 무중단으로 위키가 최신화됩니다.

