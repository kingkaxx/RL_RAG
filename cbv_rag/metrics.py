from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class EpisodeMetrics:
    correct: bool
    f1_like: float
    token_used: int
    latency_ms: int
    trap_escape: bool
    branch_count: int


TOK_RE = re.compile(r"\w+")


def _tokens(text: str) -> set[str]:
    return set(TOK_RE.findall(text.lower()))


def exact_match(pred: str, gold: str) -> bool:
    return pred.strip().lower() == gold.strip().lower()


def f1_like(pred: str, gold: str) -> float:
    p, g = _tokens(pred), _tokens(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    inter = len(p & g)
    prec = inter / len(p)
    rec = inter / len(g)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)
