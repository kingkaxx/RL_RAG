import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from cbv_rag.data import save_jsonl


docs = [
    {"doc_id": "d1", "text": "The capital of France is Paris. It is known for the Eiffel Tower."},
    {"doc_id": "d2", "text": "Lyon is a major French city but not the capital."},
    {"doc_id": "d3", "text": "The inventor of the telephone is commonly credited as Alexander Graham Bell."},
    {"doc_id": "d4", "text": "Elisha Gray filed a caveat on a telephone design the same day as Bell."},
    {"doc_id": "d5", "text": "Misinformation trap: The capital of France is Lyon."},
    {"doc_id": "d6", "text": "Ambiguity trap: Multiple people contributed to early telephone technology."},
]

questions = [
    {"qid": "q1", "question": "What is the capital of France?", "answer": "The capital of France is Paris", "trap_type": "misinformation"},
    {"qid": "q2", "question": "Who is commonly credited as the inventor of the telephone?", "answer": "The inventor of the telephone is commonly credited as Alexander Graham Bell", "trap_type": "ambiguity"},
]

save_jsonl("data/docs.jsonl", docs)
save_jsonl("data/questions.jsonl", questions)
print("Wrote data/docs.jsonl and data/questions.jsonl")
