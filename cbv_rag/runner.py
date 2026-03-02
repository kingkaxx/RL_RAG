from __future__ import annotations

import time
from dataclasses import dataclass

from .config import BudgetConfig, RetrievalConfig
from .data import Question
from .db import HybridDocDB
from .memory import BranchDAG
from .metrics import EpisodeMetrics, exact_match, f1_like
from .policies import Action
from .token_counter import count_tokens
from .verifier import HeuristicVerifier


@dataclass
class RunResult:
    policy_name: str
    qid: str
    question: str
    prediction: str
    gold: str
    correct: bool
    f1_like: float
    tokens: int
    latency_ms: int
    branches: int
    trap_escape: bool


class EpisodeRunner:
    def __init__(self, db: HybridDocDB, verifier: HeuristicVerifier, budget: BudgetConfig, retrieval: RetrievalConfig):
        self.db = db
        self.verifier = verifier
        self.budget = budget
        self.retrieval = retrieval

    def run(self, question: Question, policy, policy_name: str) -> RunResult:
        dag = BranchDAG()
        dag.add_root(question.question)

        token_used = count_tokens(question.question)
        latency_ms = 0
        verified = False
        conflict_score = 0.0
        prediction = ""

        for step in range(self.budget.max_steps):
            state = {
                "step": step,
                "max_steps": self.budget.max_steps,
                "question": question.question,
                "active_branch": dag.active_branch,
                "branches": list(dag.branches.keys()),
                "can_branch": len(dag.branches) < self.budget.max_branches,
                "have_evidence": bool(dag.tip().retrieved),
                "verified": verified,
                "conflict_score": conflict_score,
                "summary_tokens": count_tokens(dag.tip().summary),
                "token_used": token_used,
                "token_budget": self.budget.token_budget,
            }
            action: Action = policy.decide(state)

            t0 = time.time()
            if action.name == "retrieve":
                hits = self.db.search(
                    action.params["query"],
                    top_k=action.params.get("k", self.retrieval.top_k),
                    lexical_weight=self.retrieval.lexical_weight,
                    dense_weight=self.retrieval.dense_weight,
                )
                tip = dag.tip(action.params["branch"])
                tip.retrieved = hits
                if hits:
                    prediction = hits[0].text.split(".")[0]
                token_used += sum(count_tokens(h.text) for h in hits)

            elif action.name == "verify":
                tip = dag.tip(action.params["branch"])
                if tip.retrieved:
                    scores = [self.verifier.score(question.question, prediction, h.text) for h in tip.retrieved]
                    avg_support = sum(s.support for s in scores) / len(scores)
                    avg_rel = sum(s.relevance for s in scores) / len(scores)
                    conflict_score = sum(s.conflict for s in scores) / len(scores)
                    verified = avg_support > 0.5 and avg_rel > 0.4 and conflict_score < 0.5
                token_used += 20

            elif action.name == "replace":
                tip = dag.tip(action.params["branch"])
                threshold = action.params.get("threshold", 0.45)
                kept = []
                for h in tip.retrieved:
                    s = self.verifier.score(question.question, prediction, h.text)
                    if s.relevance >= threshold and s.conflict < 0.8:
                        kept.append(h)
                tip.retrieved = kept
                if kept:
                    prediction = kept[0].text.split(".")[0]
                token_used += 30

            elif action.name == "summarise":
                tip = dag.tip(action.params["branch"])
                joined = " ".join(h.text for h in tip.retrieved)
                max_tokens = action.params.get("max_tokens", 120)
                tip.summary = " ".join(joined.split()[:max_tokens])
                token_used += max_tokens

            elif action.name == "branch":
                from_bid = action.params["from_branch"]
                cf_query = f"counterfactual: not {question.question}"
                new_bid = f"b{len(dag.branches)}"
                new_nid = f"n{len(dag.nodes)}"
                dag.spawn_counterfactual(new_bid, from_bid, cf_query, new_nid)
                token_used += count_tokens(cf_query)
                dag.active_branch = new_bid

            elif action.name == "switch":
                dag.active_branch = action.params["branch"]
                token_used += 3

            elif action.name == "stop":
                break

            elapsed = int((time.time() - t0) * 1000)
            latency_ms += max(elapsed, 1)

            if token_used >= self.budget.token_budget or latency_ms >= self.budget.latency_budget_ms:
                break

        correct = exact_match(prediction, question.answer)
        f1 = f1_like(prediction, question.answer)
        trap_escape = question.trap_type != "none" and correct

        return RunResult(
            policy_name=policy_name,
            qid=question.qid,
            question=question.question,
            prediction=prediction,
            gold=question.answer,
            correct=correct,
            f1_like=f1,
            tokens=token_used,
            latency_ms=latency_ms,
            branches=len(dag.branches),
            trap_escape=trap_escape,
        )
