from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class VerifyScore:
    relevance: float
    support: float
    conflict: float


NEGATION_MARKERS = {"not", "never", "no", "none", "false", "incorrect"}
TOK_RE = re.compile(r"\w+")


def _tokens(text: str) -> set[str]:
    return set(TOK_RE.findall(text.lower()))


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _has_negation(text: str) -> bool:
    return bool(_tokens(text).intersection(NEGATION_MARKERS))


class HeuristicVerifier:
    def score(self, question: str, answer: str, evidence: str) -> VerifyScore:
        relevance = _jaccard(question, evidence)
        support = _jaccard(answer, evidence)
        conflict = 1.0 if (_has_negation(answer) ^ _has_negation(evidence)) and support > 0.2 else 0.0
        return VerifyScore(relevance=relevance, support=support, conflict=conflict)
