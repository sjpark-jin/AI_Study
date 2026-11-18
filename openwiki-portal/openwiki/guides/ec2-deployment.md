---
title: AWS EC2 프로덕션 배포 가이드
category: 가이드
tags: [AWS, EC2, Nginx, Systemd, FastAPI, Deployment]
updated: 2026-11-18
okf_version: "0.2"
summary: openwiki-portal 폴더를 AWS EC2(Ubuntu) 인스턴스에 업로드하고 Nginx 리버스 프록시 및 Systemd 서비스로 상시 운영하는 절차입니다.
infobox:
  클라우드: AWS EC2 (Ubuntu 22.04 / 24.04)
  웹 서버: Nginx (Port 80 -> 8000)
  프로세스 관리: systemd (openwiki-portal.service)
  방화벽: Security Group TCP 80, 443, 22
---

# AWS EC2 프로덕션 배포 가이드

`openwiki-portal/` 폴더에는 AWS EC2 환경에 즉시 배포할 수 있는 `deploy/setup_ec2.sh`, `deploy/nginx.conf`, `deploy/openwiki-portal.service` 파일이 포함되어 있습니다.

---

## 1. EC2 보안 그룹(Security Group) 설정
AWS 콘솔에서 EC2 인스턴스의 인바운드 규칙에 아래 포트를 허용하세요:
- **SSH (22)**: 관리자 IP
- **HTTP (80)**: `0.0.0.0/0` (위키피디아 웹 포털 접속용)
- **HTTPS (443)**: SSL/Certbot 적용 시 `0.0.0.0/0`

---

## 2. EC2에 코드 업로드 및 원클릭 설치

```bash
# 1. EC2 접속 후 저장소 클론 또는 scp로 openwiki-portal 업로드
git clone <YOUR_GITHUB_REPO_URL>
cd AI_Study/openwiki-portal

# 2. 제공된 EC2 자동 세팅 스크립트 실행
chmod +x deploy/setup_ec2.sh
sudo ./deploy/setup_ec2.sh
```

`setup_ec2.sh` 스크립트는 다음 작업을 자동으로 수행합니다:
1. Python `venv` 생성 및 `requirements.txt` 패키지 설치
2. `systemd` 서비스(`openwiki-portal.service`) 등록 및 상시 기동 (재부팅 시 자동 실행)
3. `Nginx` 리버스 프록시(`80` → `127.0.0.1:8000`) 설정 및 재시작

---

## 3. 정적 호스팅 모드 (선택)
FastAPI 백엔드 없이 Nginx만으로 순수 정적 HTML로 서빙하고 싶다면 아래 명령으로 `wiki-data.json`을 빌드한 뒤 `index.html`과 함께 Nginx 웹 루트에 배치할 수 있습니다:

```bash
python3 build_static.py
```

관련 가이드: [[guides/openwiki-workflow|LangChain OpenWiki CLI & GitHub 자동 동기화 가이드]]

