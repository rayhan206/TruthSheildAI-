# Architecture

## System Shape

```txt
Browser UI
  -> Python HTTP API
    -> Feature extraction
    -> Text risk model
    -> File/visual risk analyzer
    -> Local safety knowledge retrieval
    -> Markdown report generator
      -> Local scan artifact folder
```

## Tiers

### Web Development Tier

- Static frontend served by the Python backend.
- Pasted text input.
- Optional file upload.
- Risk dashboard.
- Evidence list.
- Markdown report viewer.

### Classical ML Tier

Implemented in `backend/engine/ml_model.py`.

The current version uses a transparent heuristic baseline with the same interface a Scikit-learn model would use later. It scores structured features such as suspicious URLs, urgency terms, money mentions, phone numbers, and trust-building language.

### Deep Learning Tier

Implemented in `backend/engine/dl_model.py`.

The current version is a visual-risk baseline for uploaded files. It can later be replaced with a PyTorch CNN for fake screenshot detection, AI-generated image detection, or manipulated document classification.

### Generative AI / RAG Tier

Implemented through:

- `backend/engine/rag_engine.py`
- `backend/engine/report_generator.py`
- `knowledge_base/scam_patterns.json`

The current version retrieves relevant scam patterns from a local knowledge base and generates a report. It can later be replaced with ChromaDB + embeddings + LLM generation.

## Storage

TruthShield Lite does not use PostgreSQL, MongoDB, or any hosted database.

```txt
storage/
  scans/
    scan_YYYYMMDD_HHMMSS_xxxxxx/
      input.txt
      features.json
      ml_result.json
      dl_result.json
      rag_context.json
      final_report.md
      scan.json
```

This keeps the project privacy-first and easy to demo.

