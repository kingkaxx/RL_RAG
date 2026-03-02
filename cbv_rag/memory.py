from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .db import RetrievalHit


@dataclass
class Node:
    node_id: str
    branch_id: str
    parent_id: Optional[str]
    query: str
    retrieved: list[RetrievalHit] = field(default_factory=list)
    summary: str = ""
    draft_answer: str = ""
    score: float = 0.0


@dataclass
class Branch:
    branch_id: str
    tip_id: str
    utility: float = 0.0


class BranchDAG:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.branches: dict[str, Branch] = {}
        self.active_branch = "b0"

    def add_root(self, query: str) -> None:
        node = Node(node_id="n0", branch_id="b0", parent_id=None, query=query)
        self.nodes[node.node_id] = node
        self.branches["b0"] = Branch(branch_id="b0", tip_id="n0")

    def tip(self, branch_id: str | None = None) -> Node:
        bid = branch_id or self.active_branch
        return self.nodes[self.branches[bid].tip_id]

    def append(self, branch_id: str, query: str, parent_id: str, node_id: str) -> Node:
        node = Node(node_id=node_id, branch_id=branch_id, parent_id=parent_id, query=query)
        self.nodes[node_id] = node
        self.branches[branch_id].tip_id = node_id
        return node

    def spawn_counterfactual(self, new_branch_id: str, from_branch: str, query_variant: str, node_id: str) -> None:
        parent = self.tip(from_branch)
        self.branches[new_branch_id] = Branch(branch_id=new_branch_id, tip_id=node_id)
        self.nodes[node_id] = Node(node_id=node_id, branch_id=new_branch_id, parent_id=parent.node_id, query=query_variant)
