"""
Week 02 FastAPI 진입점.
기동 시 문서 인제스트 수행 후 /chat 및 /session 관리 API 제공.
실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.memory import session_store
from app.rag import generate_rag_response, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    # [실수 7] 모델/DB는 기동 시 1회 준비
    n = ingest()
    print(f"[startup] Week02 인제스트 완료 청크 수: {n}")
    yield


app = FastAPI(
    title="Week02 RAG + LLM Chatbot",
    description="LLM 연동, Reranking, 대화 메모리 및 환각 방지 가드레일이 적용된 챗봇",
    version="2.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    question: str = Field(..., example="연차 휴가는 일년에 며칠 부여되나요?")
    session_id: str = Field(default="default_session", example="user_session_01")
    provider: str = Field(default="mock", example="mock")


class SourceItem(BaseModel):
    text: str
    distance: float


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[SourceItem]
    latency_ms: float
    history_count: int


@app.get("/")
def health():
    return {
        "status": "ok",
        "week": "Week 02",
        "features": ["RAG", "LLM Provider", "Reranking", "Session Memory", "Guardrails"],
        "docs_url": "/docs",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """질문에 대한 RAG+LLM 기반 자연어 답변 생성."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")
    return generate_rag_response(
        question=req.question,
        session_id=req.session_id,
        provider_name=req.provider,
    )


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """해당 세션의 대화 이력 메모리를 삭제 및 초기화."""
    success = session_store.clear_session(session_id)
    if not success:
        return {"status": "not_found", "message": f"세션 {session_id}가 존재하지 않거나 이미 비어있습니다."}
    return {"status": "success", "message": f"세션 {session_id} 메모리가 성공적으로 초기화되었습니다."}
