from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Document:
    doc_id: str
    text: str
    source: str = "local"


@dataclass
class Question:
    qid: str
    question: str
    answer: str
    trap_type: str = "none"


def load_documents(path: str | Path) -> list[Document]:
    docs: list[Document] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            docs.append(Document(**row))
    return docs


def load_questions(path: str | Path) -> list[Question]:
    qs: list[Question] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            qs.append(Question(**row))
    return qs


def save_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
