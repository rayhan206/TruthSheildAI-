# TruthShield Lite

Privacy-first AI scam, phishing, fake job offer, and suspicious document analyzer.

TruthShield Lite is a database-free full-stack project. Each scan is stored as a local artifact folder under `storage/scans`, making the system easy to inspect, demo, export, and extend.

## What It Does

- Accepts pasted suspicious text, job offers, emails, or messages.
- Optionally accepts an uploaded image, screenshot, or document-like file.
- Provides investigation modes for scam text, fake jobs, suspicious URLs, and AI media.
- Samples video frames and runs a pretrained AI-image classifier when optional AI dependencies are installed.
- Combines 70% average frame likelihood with 30% suspicious-frame ratio, then limits metadata to 10% of the final score.
- Displays the six most suspicious frames with timestamps and per-frame likelihoods.
- Shows risk category meters, highlighted evidence, local scan history, and a threat watchlist.
- Extracts text/security features.
- Produces an ML-style risk score.
- Produces a DL-style visual risk estimate for uploaded files.
- Retrieves relevant safety knowledge from a local RAG-style knowledge base.
- Generates a Markdown risk report and a dashboard result.

## Tech Stack

- Frontend: HTML, CSS, vanilla JavaScript
- Backend: Python standard library HTTP server
- Storage: local JSON and Markdown files
- AI tiers:
  - Classical ML tier: feature extraction + risk model in `backend/engine/ml_model.py`
  - Deep Learning tier: visual risk analyzer stub in `backend/engine/dl_model.py`
  - Generative AI tier: local RAG-style report generation in `backend/engine/rag_engine.py` and `report_generator.py`

This starter intentionally avoids external dependencies so it runs anywhere. Later, replace the heuristic modules with Scikit-learn, PyTorch, OCR, and a real LLM.

## Run

From the project root:

```powershell
cd truthshield-lite
python backend/app.py
```

Open:

```txt
http://localhost:8000
```

## Enable Frame-Based AI Media Detection

The basic app remains dependency-free. To enable video frame analysis, run once:

```powershell
./scripts/install-ai.ps1
```

Or install manually:

```powershell
python -m pip install -r requirements-ai.txt
```

Then restart TruthShield:

```powershell
python -B backend/app.py
```

The first image/video scan downloads the configured Hugging Face model and can take longer. Later scans reuse the local model cache.

The default model is `umm-maybe/AI-image-detector`. Override it with:

```powershell
$env:TRUTHSHIELD_AI_MODEL="your-compatible-image-classification-model"
python -B backend/app.py
```

This produces an AI-generation likelihood, not proof that media is fake. Animation, CGI, heavy compression, and unseen generators can still cause incorrect results.

## Single-File Runnable Edition

For users who want the whole demo in one file:

```powershell
python -B truthshield_compiled.py
```

This launches the same app at:

```txt
http://localhost:8000
```

The single-file edition bundles the frontend, backend routes, scanner logic, local knowledge base, and report generator into `truthshield_compiled.py`.

## Project Structure

```txt
truthshield-lite/
  truthshield_compiled.py
  backend/
    app.py
    engine/
      dl_model.py
      feature_extractor.py
      ml_model.py
      rag_engine.py
      report_generator.py
      storage.py
  frontend/
    index.html
    styles.css
    app.js
  docs/
    01-project-overview.md
    02-architecture.md
    03-runbook.md
    04-upgrade-roadmap.md
  knowledge_base/
    scam_patterns.json
  storage/
    scans/
  scripts/
    run.ps1
```

## Next Upgrade Path

1. Replace `ml_model.py` with a Scikit-learn pipeline trained on SMS spam, phishing, and fake job datasets.
2. Replace `dl_model.py` with a PyTorch CNN for fake screenshot / AI-image / manipulated document detection.
3. Replace `rag_engine.py` with ChromaDB embeddings over cybersecurity PDFs.
4. Replace `report_generator.py` with an LLM call that generates richer explanations from retrieved context.

## Documentation Order

Read these files in order:

1. `docs/01-project-overview.md`
2. `docs/02-architecture.md`
3. `docs/03-runbook.md`
4. `docs/04-upgrade-roadmap.md`
