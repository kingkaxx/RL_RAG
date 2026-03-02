from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .data import Document

TOK_RE = re.compile(r"\w+")


def tokenize(text: str) -> list[str]:
    return TOK_RE.findall(text.lower())


@dataclass
class RetrievalHit:
    doc_id: str
    text: str
    lexical_score: float
    dense_score: float
    score: float


class HybridDocDB:
    """Pure-Python hybrid retrieval DB (BM25-like + TF-IDF cosine-like)."""

    def __init__(self, docs: Sequence[Document]) -> None:
        self.docs = list(docs)
        self.doc_texts = [d.text for d in self.docs]
        self.doc_ids = [d.doc_id for d in self.docs]
        self.doc_tokens = [tokenize(t) for t in self.doc_texts]
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.avg_len = sum(self.doc_lens) / max(len(self.doc_lens), 1)

        self.df = Counter()
        for toks in self.doc_tokens:
            for term in set(toks):
                self.df[term] += 1
        self.n_docs = len(self.doc_tokens)
        self.doc_tf = [Counter(toks) for toks in self.doc_tokens]

    def _idf(self, term: str) -> float:
        return math.log(1 + (self.n_docs - self.df.get(term, 0) + 0.5) / (self.df.get(term, 0) + 0.5))

    def _bm25_like(self, q_tokens: list[str], i: int, k1: float = 1.5, b: float = 0.75) -> float:
        score = 0.0
        tf = self.doc_tf[i]
        dl = self.doc_lens[i]
        for t in q_tokens:
            f = tf.get(t, 0)
            if f == 0:
                continue
            idf = self._idf(t)
            denom = f + k1 * (1 - b + b * dl / (self.avg_len + 1e-8))
            score += idf * ((f * (k1 + 1)) / (denom + 1e-8))
        return score

    def _tfidf_cosine_like(self, q_tokens: list[str], i: int) -> float:
        q_tf = Counter(q_tokens)
        d_tf = self.doc_tf[i]
        dot = 0.0
        q_norm = 0.0
        d_norm = 0.0
        all_terms = set(q_tf) | set(d_tf)
        for t in all_terms:
            idf = self._idf(t)
            qv = q_tf.get(t, 0) * idf
            dv = d_tf.get(t, 0) * idf
            dot += qv * dv
            q_norm += qv * qv
            d_norm += dv * dv
        denom = (q_norm ** 0.5) * (d_norm ** 0.5) + 1e-8
        return dot / denom

    @staticmethod
    def _normalize(vals: list[float]) -> list[float]:
        if not vals:
            return vals
        mn, mx = min(vals), max(vals)
        if abs(mx - mn) < 1e-12:
            return [0.0 for _ in vals]
        return [(v - mn) / (mx - mn) for v in vals]

    def search(self, query: str, top_k: int = 5, lexical_weight: float = 0.5, dense_weight: float = 0.5) -> list[RetrievalHit]:
        q_tokens = tokenize(query)
        bm = [self._bm25_like(q_tokens, i) for i in range(self.n_docs)]
        ds = [self._tfidf_cosine_like(q_tokens, i) for i in range(self.n_docs)]
        bm_n = self._normalize(bm)
        ds_n = self._normalize(ds)
        final = [lexical_weight * b + dense_weight * d for b, d in zip(bm_n, ds_n)]
        ranked = sorted(range(self.n_docs), key=lambda i: final[i], reverse=True)[:top_k]

        hits: list[RetrievalHit] = []
        for i in ranked:
            hits.append(
                RetrievalHit(
                    doc_id=self.doc_ids[i],
                    text=self.doc_texts[i],
                    lexical_score=bm_n[i],
                    dense_score=ds_n[i],
                    score=final[i],
                )
            )
        return hits
