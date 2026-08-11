# 🔰 초보자를 위한 RAG LLM 애플리케이션 시작 가이드

이 가이드는 **"RAG LLM Application"** 폴더에 있는 소스 코드를 처음 접하는 분들을 위해 작성되었습니다.
복잡한 설정 없이 차근차근 따라 하시면, 최신 AI 기술인 **RAG(검색 증강 생성)**가 어떻게 작동하는지 직접 확인하실 수 있습니다.

---

## 1. 사전 준비 (Prerequisites)

이 프로젝트를 실행하기 위해서는 다음 프로그램들이 필요합니다. 이미 설치되어 있다면 건너뛰셔도 됩니다.

### 1.1 Python 설치
파이썬(Python)은 이 프로젝트가 작성된 프로그래밍 언어입니다.
- [Python 공식 홈페이지](https://www.python.org/downloads/)에서 최신 버전을 다운로드하여 설치하세요.
- **주의**: 설치 시 **"Add Python to PATH"** 옵션을 반드시 체크해주세요!

### 1.2 VS Code (Visual Studio Code) 설치
코드를 보고 실행하기 위한 편집기입니다.
- [VS Code 공식 홈페이지](https://code.visualstudio.com/)에서 다운로드하여 설치하세요.

### 1.3 UV (패키지 매니저) 설치
`uv`는 파이썬 라이브러리들을 아주 빠르고 쉽게 설치해주는 도구입니다.
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Mac/Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## 2. 프로젝트 설정 및 설치

`uv` 설치가 어렵거나 오류가 발생한다면, 파이썬에 기본으로 들어있는 `pip`를 사용하면 됩니다.

1.  **VS Code**를 실행하고, `File > Open Folder`를 눌러 **"RAG LLM Application"** 폴더를 엽니다.
2.  `Ctrl + ~` (맥은 `Cmd + ~`)를 눌러 **터미널(Terminal)**을 엽니다.
3.  터미널에 다음 명령어를 입력하여 필요한 라이브러리를 설치합니다.
    ```bash
    pip install -r requirements.txt
    ```
    (이 과정은 인터넷 속도에 따라 1~2분 정도 걸릴 수 있습니다.)


---

## 3. OpenAI API 키 설정

이 프로젝트는 OpenAI의 인공지능 모델(GPT)을 사용하므로, API 키가 필요합니다.

1.  폴더 안에 `.env.example` 파일을 찾습니다.
2.  이 파일의 이름을 `.env`로 변경합니다. (파일 우클릭 > Rename)
3.  `.env` 파일을 열고, `OPENAI_API_KEY` 부분에 여러분의 API 키를 입력합니다.
    ```
    OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
    ```
    (*API 키는 [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다.*)

---

## 4. 코드 실행해보기

초보자가 가장 쉽게 RAG를 이해할 수 있도록 **두 가지 방법**을 준비했습니다.

### 방법 A: 친절한 설명이 있는 파이썬 스크립트 실행 (추천!)
제가 특별히 초보자를 위해 주석을 달아둔 `rag_example.py` 파일을 실행해보세요.

1.  VS Code에서 `rag_example.py` 파일을 엽니다.
2.  코드를 천천히 읽어보세요. 각 줄마다 **"이 코드가 무엇을 하는지"** 한글로 자세히 적혀 있습니다.
3.  실행하려면 터미널에 다음 명령어를 입력하세요:
    ```bash
    python rag_example.py
    ```
4.  터미널에 출력되는 결과들을 보며 RAG가 어떻게 문서를 읽고, 나누고, 검색해서 답변하는지 확인해보세요.

### 방법 B: 주피터 노트북(Jupyter Notebook)으로 하나씩 실행하기
단계별로 코드를 실행하며 결과를 바로 확인하고 싶다면 노트북을 사용하세요.

1.  `02-RAG` 폴더 안에 있는 `01-RAG-Basic-PDF.ipynb` 파일을 더블 클릭합니다.
2.  VS Code가 "커널(Kernel)을 선택하세요"라고 물으면, **Python 3.x (또는 .venv)**를 선택합니다.
3.  각 코드 블록(셀) 왼쪽에 있는 **재생 버튼(▶)**을 누르면 그 부분만 실행됩니다.

---

## 5. 자주 묻는 질문 (FAQ)

**Q. `ModuleNotFoundError`가 떠요!**
A. 라이브러리 설치가 제대로 안 된 경우입니다. 터미널에 `uv sync`를 다시 입력해보세요.

**Q. API 키 오류가 발생해요.**
A. `.env` 파일에 API 키가 정확히 입력되었는지, 공백이 포함되지는 않았는지 확인해주세요.

**Q. 코드가 너무 어려워요.**
A. `rag_example.py`의 주석을 먼저 읽어보시는 것을 추천합니다. 어려운 용어(임베딩, 벡터 스토어 등)를 쉽게 풀어서 설명해 두었습니다.
