"""
Week 06 FastAPI 진입점.
- Advanced Hybrid Search (BM25 + Dense Vector + RRF)
- Cross-Encoder Reranking
- RAG Generation with Context Grounding
- Ragas RAG Triad Evaluation (Faithfulness, Relevance, Precision)
- 대화형 인터랙티브 학습 웹 UI 연동

실행: uvicorn app.main:app --reload  →  http://127.0.0.1:8000
"""
import os
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from app.hybrid_search import hybrid_retriever
    from app.reranker import reranker_engine
    from app.rag_evaluator import rag_evaluator, RAGEvaluationResult
    from app.llm import get_llm_provider
except ImportError:
    from hybrid_search import hybrid_retriever
    from reranker import reranker_engine
    from rag_evaluator import rag_evaluator, RAGEvaluationResult
    from llm import get_llm_provider

app = FastAPI(
    title="Week 06 Advanced Hybrid RAG & Evaluation Portal",
    description="BM25 + Dense Vector 하이브리드 검색, Cross-Encoder Reranker, Ragas 3대 지표 정량 평가",
    version="6.0.0",
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- 요청/응답 모델 ---
class HybridSearchRequest(BaseModel):
    query: str = Field(..., example="K8S-INGRESS-404 인그레스 에러 발생 시 조치 방법")
    top_k: int = Field(default=4, ge=1, le=10)
    dense_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.5, ge=0.0, le=1.0)


class RAGGenerateRequest(BaseModel):
    query: str = Field(..., example="AUTH-JWT-V2 통합 인증 규격과 유효시간을 알려줘.")
    use_hybrid: bool = Field(default=True)
    use_rerank: bool = Field(default=True)
    dense_weight: float = Field(default=0.5)
    bm25_weight: float = Field(default=0.5)


class DirectEvaluateRequest(BaseModel):
    query: str = Field(..., example="사내 원격 근무 보안 접속 규정")
    contexts: List[str] = Field(..., example=["원격 근무 시 모든 임직원은 사내 보안 VPN을 통해 접속해야 합니다."])
    answer: str = Field(..., example="원격 근무 시에는 반드시 사내 공인 VPN을 통해 접속해야 하며 개인 디스크 저장은 금지됩니다.")


# --- 라우트 ---
@app.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    """대화형 학습 대시보드 웹 화면을 반환합니다."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Week 06 Advanced Hybrid RAG API Running. Visit /docs</h1>")


@app.get("/api/info")
def api_info():
    """시스템 상태 및 탑재된 문서 통계 반환."""
    return {
        "status": "ok",
        "week": "Week 06",
        "features": [
            "BM25 Keyword Search",
            "Dense Vector Semantic Search",
            "RRF (Reciprocal Rank Fusion)",
            "Cross-Encoder Reranker",
            "Ragas Triad Evaluation (Faithfulness, Answer Relevance, Context Precision)",
        ],
        "indexed_docs_count": len(hybrid_retriever.documents),
        "docs_url": "/docs",
    }


@app.get("/rag/docs")
def get_knowledge_docs():
    """지식베이스에 색인된 문서 전체 목록 반환."""
    return {"documents": hybrid_retriever.documents}


@app.post("/search/hybrid")
def search_hybrid(req: HybridSearchRequest):
    """
    1) BM25 단독 검색 결과
    2) Dense Vector 단독 검색 결과
    3) RRF 하이브리드 결합 결과
    4) Cross-Encoder Reranker 최종 순위화 결과
    를 4개 컬럼으로 반환하여 검색 품질 차이를 직접 비교할 수 있도록 합니다.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")

    retrieval_res = hybrid_retriever.retrieve(
        query=req.query,
        top_k=req.top_k,
        dense_weight=req.dense_weight,
        bm25_weight=req.bm25_weight,
    )

    # Reranking 실행
    reranked = reranker_engine.rerank(
        query=req.query,
        candidate_docs=retrieval_res["hybrid_candidates"],
        top_n=req.top_k,
    )

    return {
        "query": req.query,
        "bm25_candidates": retrieval_res["bm25_candidates"],
        "dense_candidates": retrieval_res["dense_candidates"],
        "hybrid_rrf_candidates": retrieval_res["hybrid_candidates"],
        "reranked_final_candidates": reranked,
    }


@app.post("/rag/generate")
def rag_generate_and_eval(req: RAGGenerateRequest):
    """
    질문에 대해 검색(Hybrid + Reranker) -> LLM 답변 생성 -> Ragas 3대 지표 정량 평가를 일괄 수행.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")

    start_time = time.time()

    # 1. 검색 단계
    if req.use_hybrid:
        retrieval_res = hybrid_retriever.retrieve(
            query=req.query,
            top_k=4,
            dense_weight=req.dense_weight,
            bm25_weight=req.bm25_weight,
        )
        candidates = retrieval_res["hybrid_candidates"]
    else:
        # 단일 Dense 검색만 사용
        candidates = hybrid_retriever.dense.search(req.query, top_k=4, all_docs=hybrid_retriever.documents)

    # 2. Reranker 단계
    if req.use_rerank:
        top_docs = reranker_engine.rerank(req.query, candidates, top_n=3)
    else:
        top_docs = candidates[:3]

    retrieved_contexts = [f"[{d.get('title', '문서')}]\n{d.get('content', '')}" for d in top_docs]
    combined_context_text = "\n\n".join(retrieved_contexts)

    # 3. LLM 생성 단계
    llm = get_llm_provider()
    generation_prompt = (
        f"[사내 기술 문서 검색 결과]\n{combined_context_text}\n\n"
        f"[사용자 질문]\n{req.query}\n\n"
        f"반드시 위 검색된 기술 문서에만 기반하여 객관적 사실 위주로 상세하고 명확하게 답변하세요."
    )
    answer = llm.generate(
        generation_prompt,
        system_prompt="당신은 사내 IT 시스템 및 인프라 전문 AI 어시스턴트입니다.",
    )

    # 4. RAG 삼총사 평가 단계
    eval_result = rag_evaluator.evaluate_rag(
        query=req.query,
        retrieved_contexts=retrieved_contexts,
        generated_answer=answer,
    )

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "query": req.query,
        "answer": answer,
        "retrieved_documents": top_docs,
        "evaluation": eval_result,
        "latency_ms": latency_ms,
        "config": {
            "use_hybrid": req.use_hybrid,
            "use_rerank": req.use_rerank,
            "dense_weight": req.dense_weight,
            "bm25_weight": req.bm25_weight,
        },
    }


@app.post("/rag/evaluate", response_model=RAGEvaluationResult)
def direct_evaluate_rag(req: DirectEvaluateRequest):
    """
    임의의 질의, 검색 문맥 목록, 생성 답변에 대해 Ragas 3대 지표를 즉시 채점합니다.
    """
    return rag_evaluator.evaluate_rag(
        query=req.query,
        retrieved_contexts=req.contexts,
        generated_answer=req.answer,
    )
