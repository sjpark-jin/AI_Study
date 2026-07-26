"""
FastAPI 진입점. 기동 시 1회 인제스트 후 /chat 제공.
실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from app.rag import build_answer, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [실수 7] 모델/DB는 기동 시 1회만 준비. 요청마다 로드 금지.
    n = ingest()
    print(f"[startup] 인제스트 청크 수: {n}")
    yield


app = FastAPI(title="Week01 RAG Chatbot", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list


@app.get("/")
def health():
    return {"status": "ok", "hint": "POST /chat 또는 /docs 참고"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return build_answer(req.question)
