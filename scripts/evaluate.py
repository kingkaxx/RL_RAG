import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import argparse
from collections import defaultdict

from cbv_rag.config import BudgetConfig, RetrievalConfig
from cbv_rag.data import load_documents, load_questions
from cbv_rag.db import HybridDocDB
from cbv_rag.policies import CBVRAGPolicy, CounterfactualNonRLPolicy, LinearRAGPolicy
from cbv_rag.runner import EpisodeRunner
from cbv_rag.verifier import HeuristicVerifier


def p95(values: list[int]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(0.95 * (len(s) - 1))
    return float(s[idx])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default="data/docs.jsonl")
    parser.add_argument("--questions", default="data/questions.jsonl")
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--token-budget", type=int, default=2000)
    parser.add_argument("--latency-budget-ms", type=int, default=1200)
    args = parser.parse_args()

    docs = load_documents(args.docs)
    questions = load_questions(args.questions)

    db = HybridDocDB(docs)
    runner = EpisodeRunner(
        db=db,
        verifier=HeuristicVerifier(),
        budget=BudgetConfig(
            max_steps=args.max_steps,
            token_budget=args.token_budget,
            latency_budget_ms=args.latency_budget_ms,
            max_branches=2,
        ),
        retrieval=RetrievalConfig(top_k=5, lexical_weight=0.55, dense_weight=0.45),
    )

    policies = [
        ("linear_rag", LinearRAGPolicy()),
        ("counterfactual_nonrl", CounterfactualNonRLPolicy()),
        ("cbv_rag", CBVRAGPolicy()),
    ]

    rows = []
    for pname, policy in policies:
        for q in questions:
            rows.append(runner.run(q, policy, pname).__dict__)

    print("\nPer-example results")
    for r in rows:
        print(
            f"{r['policy_name']:20s} {r['qid']} correct={int(r['correct'])} "
            f"f1={r['f1_like']:.3f} tokens={r['tokens']} latency={r['latency_ms']}ms "
            f"branches={r['branches']} trap_escape={int(r['trap_escape'])}"
        )

    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        grouped[r["policy_name"]].append(r)

    print("\nAggregate")
    print("policy                acc   f1    avg_tok  p95_lat  trap_esc  avg_br")
    print("-" * 70)
    for pname, rs in grouped.items():
        n = len(rs)
        acc = sum(int(r["correct"]) for r in rs) / n
        f1 = sum(r["f1_like"] for r in rs) / n
        avg_tok = sum(r["tokens"] for r in rs) / n
        p95_lat = p95([r["latency_ms"] for r in rs])
        trap = sum(int(r["trap_escape"]) for r in rs) / n
        avg_br = sum(r["branches"] for r in rs) / n
        print(f"{pname:20s} {acc:.3f} {f1:.3f} {avg_tok:8.1f} {p95_lat:8.1f} {trap:9.3f} {avg_br:7.2f}")


if __name__ == "__main__":
    main()
