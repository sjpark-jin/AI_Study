"""
RAG 코어: 문서 인제스트 + 검색.
PLANNING.md 5절의 실수 지점들을 코드로 방어한 버전.
"""
import hashlib
import logging
import os
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("rag")

# --- 설정 ---
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
# [실수 6] 한국어 문서 대응: 경량 다국어 모델. 영어만이면 all-MiniLM-L6-v2로 교체 가능.
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CHUNK_SIZE = 500          # [실수 3] 청킹 크기(문자 기준, 단순화)
CHUNK_OVERLAP = 50
TOP_K = 3
# [실수 4,5] cosine 거리 기준. 이 값보다 멀면 "관련 문서 없음"으로 컷.
DISTANCE_THRESHOLD = 0.8


# [실수 2,7] 모델은 앱 전체에서 단 하나만 로드해 문서/질의에 동일하게 사용.
@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    log.info("임베딩 모델 로드 중(최초 1회 다운로드될 수 있음)...")
    return SentenceTransformer(EMBED_MODEL)


# [실수 1,7] PersistentClient로 재기동 후에도 유지. 컬렉션은 cosine 명시.
@lru_cache(maxsize=1)
def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name="week01_docs",
        metadata={"hnsw:space": "cosine"},  # [실수 4] 거리 공간 명시
    )


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """[실수 3] 문서 통째 임베딩 방지: 길이 기준 단순 청킹."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def _doc_id(filename: str, chunk: str) -> str:
    """[실수 1] 내용 해시 기반 ID → 재인제스트해도 중복 누적 안 됨(upsert)."""
    h = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:12]
    return f"{filename}:{h}"


def ingest() -> int:
    """app/docs/*.txt 인제스트. upsert라 매 기동 호출해도 안전."""
    if not os.path.isdir(DOCS_DIR):
        log.warning("docs 폴더 없음: %s", DOCS_DIR)
        return 0
    model, col = get_model(), get_collection()
    ids, docs, embs = [], [], []
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
    embs = model.encode(docs).tolist()  # [실수 2] 문서도 동일 모델로 임베딩
    col.upsert(ids=ids, documents=docs, embeddings=embs)  # [실수 1] add 아닌 upsert
    log.info("인제스트 완료: %d개 청크", len(docs))
    return len(docs)


def retrieve(question: str, top_k: int = TOP_K):
    """질문으로 관련 청크 검색. 임계값 넘으면 버림."""
    model, col = get_model(), get_collection()
    q_emb = model.encode([question]).tolist()  # [실수 2] 질의도 동일 모델
    res = col.query(
        query_embeddings=q_emb,
        n_results=top_k,
        include=["documents", "distances"],
    )
    docs = res["documents"][0]
    dists = res["distances"][0]
    # [실수 4,5] 거리가 작을수록 유사. 임계값 초과는 관련 없음으로 제거.
    kept = [(d, dist) for d, dist in zip(docs, dists) if dist <= DISTANCE_THRESHOLD]
    return kept


def build_answer(question: str):
    """
    검색 결과를 근거로 답변 구성.
    여기선 실제 LLM 대신 '근거 문단 반환'으로 대체(키 불필요).
    다음 주에 이 함수만 LLM 호출로 교체하면 됨.
    """
    kept = retrieve(question)
    if not kept:  # [실수 5] top-k 맹신 방지: 근거 없으면 솔직히 없다고
        return {
            "answer": "관련 근거 문서를 찾지 못했습니다. (환각 방지: 없는 내용은 답하지 않음)",
            "sources": [],
        }
    context = "\n---\n".join(d for d, _ in kept)
    answer = (
        "다음 근거 문서를 기반으로 답변합니다:\n\n" + context +
        "\n\n(※ 실제 운영에서는 이 컨텍스트를 LLM 프롬프트에 넣어 자연어 답변을 생성)"
    )
    return {
        "answer": answer,
        "sources": [{"text": d, "distance": round(dist, 4)} for d, dist in kept],
    }
