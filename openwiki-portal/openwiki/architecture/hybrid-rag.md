---
title: Advanced Hybrid RAG 파이프라인
category: 아키텍처
tags: [BM25, Dense-Vector, RRF, Cross-Encoder, Ragas]
updated: 2026-11-18
okf_version: "0.2"
summary: 단일 Dense Vector 검색의 고유명사/에러코드 누락 문제를 극복하기 위한 4단계 하이브리드 검색 및 Ragas 정량 평가 아키텍처입니다.
infobox:
  검색 방식: BM25 + Dense Vector
  순위 융합: RRF (k=60)
  재순위화: Cross-Encoder Reranker
  평가 지표: Faithfulness, Relevance, Precision
---

# Advanced Hybrid RAG 파이프라인

단일 임베딩(Dense Vector) 검색만 사용할 경우 `K8S-INGRESS-404`, `AUTH-JWT-V2`와 같은 사내 고유 에러 코드나 약어가 OOV(Out-of-Vocabulary)로 처리되어 검색 정확도가 급락하는 문제가 발생합니다.

---

## 4단계 검색 & 재순위화 파이프라인

1. **BM25 키워드 검색**: 단어 빈도(TF)와 역문서 빈도(IDF)를 계산해 정확한 에러 코드 및 고유명사를 매칭합니다.
2. **Dense Vector 의미 검색**: ChromaDB와 SentenceTransformers를 이용해 문맥적·의미적 유사 문서를 탐색합니다.
3. **RRF (Reciprocal Rank Fusion)**: 점수 척도가 다른 BM25(0~15+)와 코사인 유사도(0~1)를 순위(Rank) 역수 합산 공식으로 안전하게 결합합니다.
4. **Cross-Encoder Reranker**: 1차로 추려진 상위 4~8개 후보군에 대해서만 질문-문서 상호 어텐션(Cross-Attention)을 수행하여 지연 시간을 통제하면서도 정밀도를 극대화합니다.

---

## 관련 문서
- [[architecture/overview|AI Study 전체 아키텍처 진화 개요]]
- [[architecture/system-one-jev|TypeSafe AI Jev (System One) 정형 의사결정]]

