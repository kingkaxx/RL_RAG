from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Action:
    name: str
    params: dict


class LinearRAGPolicy:
    def decide(self, state: dict) -> Action:
        if state["step"] >= state["max_steps"] - 1:
            return Action("stop", {})
        if not state["have_evidence"]:
            return Action("retrieve", {"branch": state["active_branch"], "query": state["question"], "k": 6})
        if state["verified"]:
            return Action("stop", {})
        return Action("verify", {"branch": state["active_branch"]})


class CounterfactualNonRLPolicy:
    def decide(self, state: dict) -> Action:
        if state["step"] == 0:
            return Action("retrieve", {"branch": state["active_branch"], "query": state["question"], "k": 6})
        if state["step"] == 1 and state["can_branch"]:
            return Action("branch", {"from_branch": state["active_branch"], "mode": "counterfactual"})
        if state["step"] == 2:
            return Action("switch", {"branch": "b1" if "b1" in state["branches"] else "b0"})
        if not state["verified"]:
            return Action("verify", {"branch": state["active_branch"]})
        return Action("stop", {})


class CBVRAGPolicy:
    """Prototype learned-style policy via simple rule/value heuristics.

    This exposes the target MVP action set and branch actions.
    """

    def decide(self, state: dict) -> Action:
        if state["step"] >= state["max_steps"] - 1:
            return Action("stop", {})

        if state["token_used"] > state["token_budget"] * 0.9:
            return Action("stop", {})

        if not state["have_evidence"]:
            return Action("retrieve", {"branch": state["active_branch"], "query": state["question"], "k": 8})

        if state["conflict_score"] > 0.55 and state["can_branch"]:
            return Action("branch", {"from_branch": state["active_branch"], "mode": "counterfactual"})

        if state["conflict_score"] > 0.4:
            return Action("replace", {"branch": state["active_branch"], "threshold": 0.45})

        if not state["verified"]:
            return Action("verify", {"branch": state["active_branch"]})

        if state["summary_tokens"] > 180:
            return Action("summarise", {"branch": state["active_branch"], "max_tokens": 120})

        return Action("stop", {})
