from dataclasses import dataclass


@dataclass
class BudgetConfig:
    max_steps: int = 8
    token_budget: int = 2500
    latency_budget_ms: int = 1200
    max_branches: int = 2


@dataclass
class RetrievalConfig:
    top_k: int = 6
    dense_weight: float = 0.5
    lexical_weight: float = 0.5


@dataclass
class EvalConfig:
    trap_bonus: float = 0.5
    contradiction_penalty: float = 0.5
    verify_bonus: float = 0.2
