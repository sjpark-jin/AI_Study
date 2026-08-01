"""
Week 03 FastAPI 진입점.
AI Agent ReAct 자율 실행 API 및 등록된 도구(Tools) 조회 엔드포인트 제공.
실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import agent_engine
from app.tools import AVAILABLE_TOOLS


app = FastAPI(
    title="Week03 AI Agent & Function Calling",
    description="자율 추론(Reasoning) 및 도구 호출(Tool Calling)을 수행하는 ReAct Agent 서비스",
    version="3.0.0",
)


class AgentChatRequest(BaseModel):
    question: str = Field(..., example="김철수 책임의 잔여 연차를 확인하고 이메일로 보내줘.")
    provider: str = Field(default="mock", example="mock")


class TrajectoryStep(BaseModel):
    step: int
    thought: str
    action: str
    tool: Optional[str] = None
    kwargs: Optional[Dict[str, Any]] = None
    observation: str


class AgentChatResponse(BaseModel):
    question: str
    final_answer: str
    trajectory: List[TrajectoryStep]
    total_steps: int
    latency_ms: float


@app.get("/")
def health():
    return {
        "status": "ok",
        "week": "Week 03",
        "features": ["AI Agent", "ReAct Pattern", "Function Calling", "Multi-Tool Execution"],
        "available_tools_count": len(AVAILABLE_TOOLS),
        "docs_url": "/docs",
    }


@app.get("/agent/tools")
def list_tools():
    """Agent가 구동 가능한 전체 외부 도구(Tools) 목록과 파라미터 스키마를 반환."""
    tool_list = []
    for name, info in AVAILABLE_TOOLS.items():
        tool_list.append({
            "name": name,
            "description": info["description"],
            "parameters": info["parameters"],
        })
    return {"tools": tool_list}


@app.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat(req: AgentChatRequest):
    """사용자의 질의를 ReAct Agent가 추론하여 적절한 도구를 선택/실행한 후 최종 답변 반환."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")
    
    result = agent_engine.run(
        question=req.question,
        provider_name=req.provider,
    )
    return result
