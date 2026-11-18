# OpenWiki Wikipedia Portal (LangChain OpenWiki + AWS EC2)

LangChain의 **OpenWiki (`langchain-ai/openwiki`)**로 GitHub 저장소 내 `openwiki/` 폴더에 생성·유지보수되는 마크다운(`.md`) 문서들을 읽어와, **위키피디아(Wikipedia) 형태의 지식 백과 홈페이지(`index.html`)**로 제공하는 포털입니다.

---

## 📁 폴더 구성

```text
openwiki-portal/
├── index.html                  # 위키피디아 스타일 SPA 웹 포털 (동적 API + 정적 JSON 겸용)
├── requirements.txt            # FastAPI, Uvicorn, Requests 등 Python 의존성
├── build_static.py             # Nginx 단독 정적 서빙용 wiki-data.json 번들 빌더
├── .env.example / .env         # 로컬 폴더 및 GitHub 저장소 동기화 설정
├── app/
│   ├── main.py                 # FastAPI 웹 서버 및 REST API
│   └── wiki_loader.py          # .md 파서 (YAML Front Matter, 목차, 위키링크, 백링크, GitHub API)
├── openwiki/                   # LangChain OpenWiki(OKF v0.2) 표준 .md 위키 폴더
│   ├── index.md                # 루트 인덱스 문서
│   ├── logs.md                 # OpenWiki 변경 감사 로그
│   ├── architecture/           # 아키텍처 문서들 (.md)
│   └── guides/                 # 운영 및 배포 가이드 (.md)
└── deploy/                     # AWS EC2 배포용 설정 모음
    ├── setup_ec2.sh            # Ubuntu EC2 원클릭 설치 스크립트
    ├── nginx.conf              # Nginx 80 -> 8000 리버스 프록시 설정
    └── openwiki-portal.service # systemd 상시 실행 서비스 유닛
```

---

## 🛠️ 1. LangChain OpenWiki CLI로 GitHub 저장소에 `.md` 생성하기

```bash
# 1) Node.js 22.22+ 환경에서 OpenWiki 전역 설치
npm install -g openwiki

# 2) GitHub 저장소 루트에서 위키 폴더(openwiki/) 초기화
openwiki --init

# 3) 이후 코드 변경(git diff) 시 증분 업데이트
openwiki --update
```

---

## 💻 2. 로컬 실행 및 테스트

```bash
# 저장소 루트의 가상환경 활성화
cd /Users/sangjin/Desktop/workspace/AI_Study
source venv/bin/activate

# openwiki-portal 실행
cd openwiki-portal
uvicorn app.main:app --reload
```
- 웹 홈페이지: http://127.0.0.1:8000
- Swagger API 문서: http://127.0.0.1:8000/docs
- 웹 상단의 **`🔄 GitHub 동기화`** 버튼을 누르면 원하는 GitHub 저장소(`owner/repo`)의 `openwiki` 폴더 내 `.md` 파일들을 실시간으로 가져와 위키피디아 화면에 반영할 수 있습니다.

---

## ☁️ 3. AWS EC2 배포 방법

### 방법 A: FastAPI + Nginx + Systemd 풀스택 배포 (권장)
1. AWS EC2(Ubuntu 22.04 / 24.04) 보안 그룹에서 **TCP 80 (HTTP)** 인바운드를 허용합니다.
2. EC2에 `openwiki-portal/` 폴더를 업로드(`git clone` 또는 `scp`)한 뒤 원클릭 스크립트를 실행합니다:
   ```bash
   cd openwiki-portal
   chmod +x deploy/setup_ec2.sh
   sudo ./deploy/setup_ec2.sh
   ```
3. 브라우저에서 `http://<EC2_PUBLIC_IP>`로 접속합니다.

### 방법 B: 순수 정적 파일(Nginx 단독 / S3) 배포
Python 서버를 띄우지 않고 `index.html`과 `wiki-data.json`만으로 서빙하고 싶다면:
```bash
python3 build_static.py
# 생성된 wiki-data.json과 index.html을 Nginx 웹 루트(/var/www/html)에 복사
```

