---
title: OpenWiki 변경 로그 (logs.md)
category: 메타
tags: [Changelog, Git-Diff, OpenWiki, Audit]
updated: 2026-11-18
okf_version: "0.2"
summary: OpenWiki가 Git 커밋 이력과 코드 diff를 분석하여 위키 문서를 자동 생성 및 갱신한 감사 로그입니다.
infobox:
  파일 역할: OKF 예약 로그 문서 (logs.md)
  추적 방식: Git Commit & Diff 기반 증분 업데이트
  최신 갱신: 2026-11-18
---

# OpenWiki 변경 로그 (`logs.md`)

LangChain **OpenWiki**는 한 번 작성되고 방치되는 정적 문서를 방지하기 위해, 저장소의 커밋 이력(`git diff`)을 기반으로 변경된 모듈만 증분 업데이트하고 그 이력을 `logs.md`에 기록합니다.

---

## 2026-11-18 — 초기 위키 포털 부트스트랩 (`openwiki --init`)
- **생성된 루트 문서**: [[index|index.md]] (OKF v0.2 인덱스)
- **생성된 아키텍처 문서**:
  - [[architecture/overview|architecture/overview.md]]
  - [[architecture/hybrid-rag|architecture/hybrid-rag.md]]
  - [[architecture/system-one-jev|architecture/system-one-jev.md]]
- **생성된 운영 가이드**:
  - [[guides/openwiki-workflow|guides/openwiki-workflow.md]]
  - [[guides/ec2-deployment|guides/ec2-deployment.md]]

---

## 자동 갱신 파이프라인 연결 방법
GitHub 저장소에 코드가 Push될 때 아래 명령이 실행되도록 설정하면, PR 또는 커밋 단위로 이 파일이 자동 업데이트됩니다:

```bash
npm install -g openwiki
openwiki --update
```

자세한 설정 방법은 [[guides/openwiki-workflow|LangChain OpenWiki CLI & GitHub 자동 동기화 가이드]]를 참조하세요.

