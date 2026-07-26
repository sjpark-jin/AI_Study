"""
Week 2 RAG 코어: 문서 인제스트 + 2단계 Reranking 검색 + 대화 메모리 + LLM 연동.
PLANNING.md 5절의 실수 지점들을 코드로 방어한 고도화 버전.
"""
import hashlib
import logging
import os
import time
from functools import lru_cache
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

from app.llm import get_llm_provider
from app.memory import session_store

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rag")

# --- 설정 ---
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
TOP_K_INITIAL = 5
TOP_K_RERANKED = 3
DISTANCE_THRESHOLD = 0.85

SYSTEM_PROMPT = """너는 사내 규정 및 문서 지식을 기반으로 친절하게 답변하는 AI 어시스턴트이다.
아래 [엄격 준수 규칙]을 반드시 따라야 한다.

[엄격 준수 규칙]:
1. 제공된 [참조 컨텍스트]에 기재된 정보만을 근거로 답변하라.
2. [참조 컨텍스트]에 언급되지 않은 사실을 임의로 상상하거나 추측하여 답변하지 마라 (환각 엄격 금지).
3. 근거가 부족하거나 내용이 없는 경우, "제공된 사내 규정 문서에서 관련 내용을 찾을 수 없습니다."라고 솔직히 밝혀라.
4. 사용자 질문에 명확하고 정돈된 한국어 어조로 답변하라.
"""


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    log.info("임베딩 모델 로드 중(최초 1회)...")
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name="week02_policy_docs",
        metadata={"hnsw:space": "cosine"},
    )


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def _doc_id(filename: str, chunk: str) -> str:
    h = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:12]
    return f"{filename}:{h}"


def ingest() -> int:
    """app/docs/*.txt 문서 인제스트."""
    if not os.path.isdir(DOCS_DIR):
        log.warning("docs 폴더 없음: %s", DOCS_DIR)
        return 0
    model, col = get_model(), get_collection()
    ids, docs = [], []
    for fn in os.listdir(DOCS_DIR):
        if not fn.endswith(".txt"):
            continue
        with open(os.path.join(DOCS_DIR, fn), encoding="utf-8") as f:
            for chunk in chunk_text(f.read()):
                ids.append(_doc_id(fn, chunk))
                docs.append(chunk)
    if not docs:
        log.info("인제스트할 문서 없음.")
        return 0
    embs = model.encode(docs).tolist()
    col.upsert(ids=ids, documents=docs, embeddings=embs)
    log.info("인제스트 완료: %d개 청크", len(docs))
    return len(docs)


def rerank_documents(question: str, candidate_docs: List[tuple]) -> List[tuple]:
    """
    [실수 4 방어] 2차 Reranking 단계:
    1차 벡터 검색 결과에 대해 키워드 매칭 보너스 점수를 반영하여 재순위화.
    """
    if not candidate_docs:
        return []

    q_keywords = [k for k in question.split() if len(k) > 1]
    scored_docs = []

    for doc, dist in candidate_docs:
        # 코사인 거리(작을수록 좋음)에 키워드 매칭 보너스 차감
        overlap_count = sum(1 for kw in q_keywords if kw in doc)
        score = dist - (overlap_count * 0.05)  # 키워드가 겹치면 거리를 더 가깝게 보정
        scored_docs.append((doc, dist, score))

    # 보정 점수 기준 오름차순 정렬 (거리가 작을수록 우수)
    scored_docs.sort(key=lambda x: x[2])
    
    # 상위 TOP_K_RERANKED개 반환
    return [(doc, dist) for doc, dist, _ in scored_docs[:TOP_K_RERANKED]]


def retrieve_and_rerank(question: str) -> List[tuple]:
    """1차 Vector 검색 + 2차 Reranking 결합 검색."""
    model, col = get_model(), get_collection()
    q_emb = model.encode([question]).tolist()
    res = col.query(
        query_embeddings=q_emb,
        n_results=TOP_K_INITIAL,
        include=["documents", "distances"],
    )
    docs = res["documents"][0]
    dists = res["distances"][0]
    
    # 임계값 필터링 (거리 > DISTANCE_THRESHOLD 버림)
    candidates = [(d, dist) for d, dist in zip(docs, dists) if dist <= DISTANCE_THRESHOLD]
    
    # 2차 Reranking 적용
    return rerank_documents(question, candidates)


def generate_rag_response(question: str, session_id: str = "default_session", provider_name: str = "mock") -> Dict[str, Any]:
    """
    전체 RAG 파이프라인 수행:
    Session History 조회 -> Retrieval & Rerank -> LLM 호출 -> Session History 저장
    """
    start_time = time.time()

    # 1. 이전 대화 기록 가져오기
    history = session_store.get_history(session_id)

    # 2. 관련 문서 검색 & 재순위화
    kept = retrieve_and_rerank(question)

    if not kept:
        answer = "제공된 사내 규정 문서에서 해당 질문에 대한 연관 내용을 찾지 못했습니다. (환각 방지: 지식베이스 외 답변 거부)"
        sources = []
    else:
        context_text = "\n---\n".join(d for d, _ in kept)
        
        # 3. LLM Provider 호출하여 답변 생성
        llm = get_llm_provider(provider_name)
        answer = llm.generate(
            system_prompt=SYSTEM_PROMPT,
            history=history,
            question=question,
            context=context_text,
        )
        sources = [{"text": d, "distance": round(dist, 4)} for d, dist in kept]

    # 4. 세션 대화 이력 업데이트 (질문 & 답변)
    session_store.add_message(session_id, "user", question)
    session_store.add_message(session_id, "assistant", answer)

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "answer": answer,
        "session_id": session_id,
        "sources": sources,
        "latency_ms": latency_ms,
        "history_count": len(session_store.get_history(session_id)),
    }
