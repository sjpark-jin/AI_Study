"""
Week 04 FastAPI 진입점.
Multi-Agent 파이프라인 자율 실행 및 상태 워크플로 조회 API 제공.
실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from app.orchestrator import orchestrator
except ImportError:
    from orchestrator import orchestrator


app = FastAPI(
    title="Week04 Multi-Agent System",
    description="역할 분담 에이전트(Planner, Researcher, Reviewer)와 상태 머신 기반 협업 시스템",
    version="4.0.0",
)


class MultiAgentRequest(BaseModel):
    user_request: str = Field(..., example="김철수 책임의 연차를 확인하고 이메일로 송신해줘.")


class MultiAgentResponse(BaseModel):
    user_request: str
    final_answer: str
    status: str
    plan: List[str]
    findings_count: int
    workflow_history: List[Dict[str, Any]]
    total_revisions: int
    latency_ms: float


@app.get("/")
def health():
    return {
        "status": "ok",
        "week": "Week 04",
        "features": ["Multi-Agent System", "Planner-Researcher-Reviewer", "State Machine Orchestration"],
        "docs_url": "/docs",
    }


@app.get("/multiagent/graph")
def get_graph():
    """상태 머신의 노드 및 흐름 구조 정보를 반환한다."""
    return {
        "nodes": [
            {"id": "START", "description": "사용자 요청 수신"},
            {"id": "PLAN", "description": "PlannerAgent: 실행 계획 수립"},
            {"id": "RESEARCH", "description": "ResearcherAgent: RAG/DB 근거 데이터 수집"},
            {"id": "REVIEW", "description": "ReviewerAgent: 위험 요소 및 품질 검수"},
            {"id": "FINISH", "description": "최종 답변 완료 및 반환"},
        ],
        "edges": [
            {"from": "START", "to": "PLAN"},
            {"from": "PLAN", "to": "RESEARCH"},
            {"from": "RESEARCH", "to": "REVIEW"},
            {"from": "REVIEW", "to": "FINISH", "condition": "APPROVED"},
            {"from": "REVIEW", "to": "RESEARCH", "condition": "REJECTED (재시도)"},
        ],
    }


@app.post("/multiagent/run", response_model=MultiAgentResponse)
def run_multi_agent(req: MultiAgentRequest):
    """멀티 에이전트 협업 워크플로를 수행하고 결과를 반환한다."""
    if not req.user_request.strip():
        raise HTTPException(status_code=400, detail="요청 내용을 입력해주세요.")
    return orchestrator.run_workflow(req.user_request)
