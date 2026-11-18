"""
Week 06 Hybrid Search (하이브리드 검색) 엔진 모듈.
1) BM25 키워드 정확도 검색 (품번, 고유명사, 에러코드, 약어 특화)
2) Dense Vector 의미 유사도 검색 (ChromaDB + SentenceTransformers)
3) RRF (Reciprocal Rank Fusion) 상호 순위 결합 알고리즘
"""
import math
import os
import re
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter

log = logging.getLogger("hybrid_search")

DOCS_FILE = os.path.join(os.path.dirname(__file__), "docs", "sample_tech_docs.txt")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def tokenize_text(text: str) -> List[str]:
    """
    한글, 영문, 특수문자가 포함된 코드(K8S-INGRESS-404, AUTH-JWT-V2 등)를 보존하는 정교한 토크나이저.
    """
    # 1. 원본 영숫자-하이픈 복합어 보존 (예: K8S-INGRESS-404, GPU-A100-CUDA12)
    compound_tokens = re.findall(r"[A-Za-z0-9]+-[A-Za-z0-9\-]+", text)
    # 2. 일반 단어 분절 (한글, 영문, 숫자)
    words = re.findall(r"[가-힣A-Za-z0-9]+", text.lower())
    return [t.lower() for t in compound_tokens] + words


class BM25Searcher:
    """
    순수 Python/수식 기반 Okapi BM25 검색기.
    외부 무거운 라이브러리 없이도 완벽한 BM25 점수 산출 및 교육용 동작 원리 파악이 가능합니다.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.corpus_size: int = 0
        self.avgdl: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_tokens: List[List[str]] = []

    def fit(self, docs: List[Dict[str, Any]]):
        self.documents = docs
        self.corpus_size = len(docs)
        self.doc_tokens = [tokenize_text(d["content"]) for d in docs]
        
        total_len = sum(len(tokens) for tokens in self.doc_tokens)
        self.avgdl = total_len / max(1, self.corpus_size)

        # 단어별 등장 문서 수(Document Frequency) 계산
        self.doc_freqs = Counter()
        for tokens in self.doc_tokens:
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] += 1

        # IDF(Inverse Document Frequency) 계산
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # BM25 표준 IDF 공식
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self.documents:
            return []
        
        query_tokens = tokenize_text(query)
        scores = []

        for idx, tokens in enumerate(self.doc_tokens):
            score = 0.0
            doc_len = len(tokens)
            term_counts = Counter(tokens)

            for q_term in query_tokens:
                if q_term not in term_counts:
                    continue
                tf = term_counts[q_term]
                idf = self.idf.get(q_term, 0.0)
                # BM25 항 가중치 계산
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1e-6, self.avgdl)))
                score += idf * (numerator / denominator)

            scores.append((idx, score))

        # 점수 기준 내림차순 정렬
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for rank, (idx, score) in enumerate(scores[:top_k], 1):
            doc = self.documents[idx].copy()
            doc["bm25_score"] = round(score, 4)
            doc["bm25_rank"] = rank
            results.append(doc)

        return results


class DenseVectorSearcher:
    """
    ChromaDB 및 SentenceTransformers를 활용한 Dense Vector 문맥 유사도 검색기.
    """
    def __init__(self):
        self._model = None
        self._collection = None
        self.documents: List[Dict[str, Any]] = []

    def _init_chroma(self, docs: List[Dict[str, Any]]):
        if self._collection is not None:
            return
        
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            log.info("[DenseVector] 임베딩 모델 로드 중: %s", EMBED_MODEL_NAME)
            self._model = SentenceTransformer(EMBED_MODEL_NAME)

            client = chromadb.PersistentClient(path=CHROMA_DIR)
            self._collection = client.get_or_create_collection(
                name="week06_hybrid_docs",
                metadata={"hnsw:space": "cosine"},
            )

            # 인덱싱 (기존 문서가 없을 때)
            if self._collection.count() == 0 and docs:
                log.info("[DenseVector] ChromaDB 문서 인덱싱 진행 (%d건)", len(docs))
                ids = [d["doc_id"] for d in docs]
                contents = [d["content"] for d in docs]
                metadatas = [{"title": d["title"]} for d in docs]
                embeddings = self._model.encode(contents).tolist()

                self._collection.upsert(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
        except Exception as e:
            log.warning("[DenseVector] ChromaDB 로드 실패 (Fallback 모드로 전환): %s", e)

    def search(self, query: str, top_k: int = 4, all_docs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        self._init_chroma(all_docs or [])

        # 실제 ChromaDB 및 SentenceTransformer 가용 시
        if self._collection is not None and self._model is not None:
            try:
                q_emb = self._model.encode([query]).tolist()
                res = self._collection.query(query_embeddings=q_emb, n_results=top_k)
                results = []
                if res and "ids" in res and res["ids"]:
                    ids = res["ids"][0]
                    docs = res["documents"][0]
                    distances = res["distances"][0]
                    metas = res["metadatas"][0]

                    for rank, (doc_id, content, dist, meta) in enumerate(zip(ids, docs, distances, metas), 1):
                        similarity = round(1.0 - dist, 4)  # cosine distance -> similarity
                        results.append({
                            "doc_id": doc_id,
                            "title": meta.get("title", ""),
                            "content": content,
                            "dense_score": similarity,
                            "dense_rank": rank,
                        })
                return results
            except Exception as e:
                log.warning("Chroma 쿼리 중 에러 발생: %s", e)

        # Fallback (의미 키워드 매칭 기반 모의 벡터 점수 산출)
        results = []
        q_lower = query.lower()
        for idx, d in enumerate(all_docs or [], 1):
            score = 0.5
            if any(k in d["content"].lower() for k in q_lower.split()):
                score += 0.35
            results.append({
                "doc_id": d["doc_id"],
                "title": d["title"],
                "content": d["content"],
                "dense_score": round(score, 4),
                "dense_rank": idx,
            })
        results.sort(key=lambda x: x["dense_score"], reverse=True)
        for rank, r in enumerate(results[:top_k], 1):
            r["dense_rank"] = rank
        return results[:top_k]


class HybridRetriever:
    """
    BM25(키워드)와 Dense Vector(문맥 의미) 검색을 통합하고
    RRF(Reciprocal Rank Fusion) 상호 순위 융합을 수행하는 하이브리드 리트리버.
    """
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.bm25 = BM25Searcher()
        self.dense = DenseVectorSearcher()
        self.documents: List[Dict[str, Any]] = []
        self._load_corpus()

    def _load_corpus(self):
        """sample_tech_docs.txt 파일을 파싱하여 코퍼스를 적재합니다."""
        if not os.path.isfile(DOCS_FILE):
            log.error("샘플 문서 파일이 존재하지 않습니다: %s", DOCS_FILE)
            return

        with open(DOCS_FILE, "r", encoding="utf-8") as f:
            raw_text = f.read()

        blocks = raw_text.split("---")
        parsed_docs = []
        for b in blocks:
            text = b.strip()
            if not text:
                continue
            
            # 파싱: [문서 ID: XXX], 제목: YYY, 내용: ZZZ
            doc_id_match = re.search(r"\[문서 ID:\s*([A-Za-z0-9\-]+)\]", text)
            title_match = re.search(r"제목:\s*(.+)", text)
            content_match = re.search(r"내용:\s*([\s\S]+)", text)

            doc_id = doc_id_match.group(1) if doc_id_match else f"DOC-{len(parsed_docs)+1}"
            title = title_match.group(1).strip() if title_match else "사내 기술 문서"
            content = content_match.group(1).strip() if content_match else text

            parsed_docs.append({
                "doc_id": doc_id,
                "title": title,
                "content": content,
            })

        self.documents = parsed_docs
        self.bm25.fit(self.documents)
        log.info("[HybridRetriever] 총 %d개의 기술 문서 코퍼스 적재 완료", len(self.documents))

    def retrieve(self, query: str, top_k: int = 4, dense_weight: float = 0.5, bm25_weight: float = 0.5) -> Dict[str, Any]:
        """
        하이브리드 검색을 수행하고 RRF 점수로 융합된 최종 후보 목록을 반환합니다.
        """
        # 1. BM25 검색
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        # 2. Dense Vector 검색
        dense_results = self.dense.search(query, top_k=top_k * 2, all_docs=self.documents)

        # 3. RRF (Reciprocal Rank Fusion) 융합 점수 계산
        # RRF_Score = sum(weight / (k + rank))
        fusion_map: Dict[str, Dict[str, Any]] = {}

        for doc in dense_results:
            did = doc["doc_id"]
            dense_rank = doc["dense_rank"]
            rrf_contrib = dense_weight * (1.0 / (self.rrf_k + dense_rank))
            fusion_map[did] = {
                "doc_id": did,
                "title": doc["title"],
                "content": doc["content"],
                "dense_rank": dense_rank,
                "dense_score": doc["dense_score"],
                "bm25_rank": None,
                "bm25_score": 0.0,
                "rrf_score": rrf_contrib,
            }

        for doc in bm25_results:
            did = doc["doc_id"]
            bm25_rank = doc["bm25_rank"]
            rrf_contrib = bm25_weight * (1.0 / (self.rrf_k + bm25_rank))
            if did in fusion_map:
                fusion_map[did]["bm25_rank"] = bm25_rank
                fusion_map[did]["bm25_score"] = doc["bm25_score"]
                fusion_map[did]["rrf_score"] += rrf_contrib
            else:
                fusion_map[did] = {
                    "doc_id": did,
                    "title": doc["title"],
                    "content": doc["content"],
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "bm25_rank": bm25_rank,
                    "bm25_score": doc["bm25_score"],
                    "rrf_score": rrf_contrib,
                }

        # 융합 점수 기준 정렬
        hybrid_ranked = sorted(fusion_map.values(), key=lambda x: x["rrf_score"], reverse=True)
        for rank, item in enumerate(hybrid_ranked, 1):
            item["hybrid_rank"] = rank
            item["rrf_score"] = round(item["rrf_score"], 6)

        return {
            "query": query,
            "bm25_candidates": bm25_results[:top_k],
            "dense_candidates": dense_results[:top_k],
            "hybrid_candidates": hybrid_ranked[:top_k],
        }


# 싱글톤 인스턴스 생성
hybrid_retriever = HybridRetriever()
