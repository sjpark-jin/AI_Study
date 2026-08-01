"""
Week 3 RAG 도우미: ChromaDB 기반 간단 검색 기능.
"""
import os
import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

_model = None
_col = None


def _init_rag():
    global _model, _col
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    if _col is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _col = client.get_or_create_collection(
            name="week03_agent_docs",
            metadata={"hnsw:space": "cosine"},
        )
        # 인제스트
        if os.path.isdir(DOCS_DIR):
            for fn in os.listdir(DOCS_DIR):
                if fn.endswith(".txt"):
                    filepath = os.path.join(DOCS_DIR, fn)
                    with open(filepath, encoding="utf-8") as f:
                        text = f.read()
                        _col.upsert(
                            ids=[fn],
                            documents=[text],
                            embeddings=_model.encode([text]).tolist(),
                        )


def search_docs(query: str, top_k: int = 2) -> list:
    _init_rag()
    q_emb = _model.encode([query]).tolist()
    res = _col.query(query_embeddings=q_emb, n_results=top_k)
    return res["documents"][0] if res and "documents" in res else []
