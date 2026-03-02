# CBV-RAG Prototype (MVP + Baselines)

Runnable **Counterfactual Branch-and-Verify RAG (CBV-RAG)** prototype with baselines, token accounting, and local retrieval DB suitable for HPC.

## Included
- `cbv_rag/` core implementation.
- Local hybrid retrieval DB (pure Python BM25-like + TF-IDF cosine-like).
- Baselines:
  - `linear_rag`
  - `counterfactual_nonrl`
  - `cbv_rag`
- Evaluation script with accuracy/F1-like + token + latency + trap-escape reporting.

## Quick start
```bash
python scripts/make_toy_data.py
PYTHONPATH=. python scripts/evaluate.py
```

## Run on your own data
- Docs: `data/docs.jsonl`
- Questions: `data/questions.jsonl`

### `docs.jsonl`
```json
{"doc_id":"d1","text":"...","source":"local"}
```

### `questions.jsonl`
```json
{"qid":"q1","question":"...","answer":"...","trap_type":"misinformation"}
```

## Notes
- No external Python dependencies required.
- Designed for easy extension to PPO/GRPO controller later.
- Token budget and latency budget are enforced per-episode.
