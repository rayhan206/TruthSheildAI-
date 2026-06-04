# Upgrade Roadmap

## Phase 1: Scikit-learn Model

Replace `backend/engine/ml_model.py` with a trained Scikit-learn pipeline.

Suggested datasets:

- SMS spam datasets
- Phishing email datasets
- Fake job posting datasets
- URL phishing datasets

Suggested models:

- Logistic Regression
- Random Forest
- Linear SVM
- Gradient Boosting

## Phase 2: OCR + Document Intelligence

Add OCR for screenshots and PDFs.

Suggested tools:

- Tesseract
- EasyOCR
- PyMuPDF

New flow:

```txt
Uploaded screenshot/PDF -> OCR -> extracted text -> text risk model + RAG report
```

## Phase 3: PyTorch Visual Model

Replace `backend/engine/dl_model.py` with a CNN or fine-tuned image model.

Possible tasks:

- Fake screenshot detection
- AI-generated image detection
- Manipulated document classification
- Scam template classification

## Phase 4: Real RAG + LLM

Replace the local keyword retriever with:

- ChromaDB
- Sentence-transformer embeddings
- Cybersecurity/scam-awareness PDFs
- LLM-generated explanations

## Phase 5: Production Hardening

- Dockerfile
- Tests
- Rate limiting
- File size limits
- Malware-safe upload handling
- Export/delete scan controls
- Optional encrypted local storage

