# AI Study — 주차별 AI/아키텍처 실습 및 학습 로드맵

주 1회 AI/아키텍처 프로젝트를 직접 구축해보며 기술적 이해와 IT 기획/아키텍처 관점의 실무 체크포인트를 정리하는 커리큘럼 저장소입니다.

---

## 📅 주차별 학습 과제 목록 (Curriculum)

| 주차 | 주제 | 핵심 키워드 & 기술 스택 | 링크 |
|:---:|:---|:---|:---:|
| **Week 01** | **최소 RAG 챗봇 직접 구성하기** | FastAPI, ChromaDB, SentenceTransformers, Vector Embeddings | [Week 01 이동](file:///Users/sangjin/Desktop/workspace/AI_Study/week-01/README.md) |
| **Week 02** | **RAG + LLM 연동 및 프롬프트/메모리 고도화** | LLM Provider (Mock/OpenAI/Ollama), Reranking, Session Memory, Guardrails | [Week 02 이동](file:///Users/sangjin/Desktop/workspace/AI_Study/week-02/README.md) |

---

## 🚀 빠른 시작 (Quick Start)

원하는 주차 폴더로 이동하여 독립된 Python 환경에서 실행할 수 있습니다:

### Week 01 실행
```bash
cd week-01
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Week 02 실행
```bash
cd week-02
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 💡 저장소 운영 규칙 (`drafts/`)
- 매주 토요일 GitHub Actions 워크플로(`.github/workflows/weekly-publish.yml`)가 `drafts/` 창고에 준비된 다음 주차 학습 내용을 루트로 자동으로 공개 발행합니다.
- 사전 준비 과제는 `drafts/week-XX` 형식으로 추가됩니다.
