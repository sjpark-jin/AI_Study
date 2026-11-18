"""
Week 06 Reranker (Cross-Encoder 재순위화) 모듈.
1차 하이브리드 검색으로 도출된 후보 문서군(Top-K)을
질문(Query)과 문서(Document) 간의 전방위 상호 주의집중(Cross-Attention) 메커니즘을 통해
정밀 재채점(Reranking)하여 최적의 상위 문서를 선별합니다.
"""
import logging
from typing import List, Dict, Any

log = logging.getLogger("reranker")

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """
    Cross-Encoder 기반 정밀 재순위화 엔진.
    질문과 문서 본문을 결합하여 토큰 레벨의 문맥 연관도를 재계산합니다.
    """
    def __init__(self, model_name: str = CROSS_ENCODER_MODEL):
        self.model_name = model_name
        self._model = None
        self._initialized = False

    def _init_model(self):
        if self._initialized:
            return
        try:
            from sentence_transformers import CrossEncoder
            log.info("[Reranker] Cross-Encoder 모델 로딩 중: %s", self.model_name)
            self._model = CrossEncoder(self.model_name)
            self._initialized = True
        except Exception as e:
            log.warning("[Reranker] Cross-Encoder 로드 실패 (휴리스틱 채점기 모드로 작동): %s", e)
            self._initialized = True

    def rerank(self, query: str, candidate_docs: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        후보 문서 목록을 질문과의 상호 연관성 점수로 정밀 재순위화합니다.
        """
        if not candidate_docs:
            return []
        
        self._init_model()

        # 1. 실제 Cross-Encoder 모델이 가용한 경우
        if self._model is not None:
            try:
                pairs = [[query, doc["content"]] for doc in candidate_docs]
                scores = self._model.predict(pairs)

                scored_docs = []
                for doc, score in zip(candidate_docs, scores):
                    d_copy = doc.copy()
                    d_copy["rerank_score"] = round(float(score), 4)
                    scored_docs.append(d_copy)

                scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
                for rank, d in enumerate(scored_docs[:top_n], 1):
                    d["final_rank"] = rank
                return scored_docs[:top_n]
            except Exception as e:
                log.warning("[Reranker] Cross-Encoder 추론 중 에러 발생: %s", e)

        # 2. 휴리스틱 / 모의 Reranker (교육용 시뮬레이션 및 로컬 빠른 실행)
        scored_docs = []
        q_words = set(query.lower().split())

        for doc in candidate_docs:
            d_copy = doc.copy()
            content_lower = d_copy["content"].lower()
            title_lower = d_copy["title"].lower()

            # 질문 단어의 제목 출현 가중치 (3.0배) + 본문 출현 빈도 + RRF 결합 점수
            exact_matches = sum(2.5 for w in q_words if w in title_lower)
            body_matches = sum(1.2 for w in q_words if w in content_lower)
            rrf_contrib = d_copy.get("rrf_score", 0.0) * 100.0

            heuristic_score = round(exact_matches + body_matches + rrf_contrib, 4)
            d_copy["rerank_score"] = heuristic_score
            scored_docs.append(d_copy)

        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        for rank, d in enumerate(scored_docs[:top_n], 1):
            d["final_rank"] = rank

        return scored_docs[:top_n]


# 싱글톤 인스턴스
reranker_engine = CrossEncoderReranker()
