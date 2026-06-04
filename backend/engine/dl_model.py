def analyze_uploaded_file(file_meta, file_bytes):
    if not file_meta or file_bytes is None:
        return {
            "visual_risk_score": 0,
            "visual_risk_level": "Not analyzed",
            "model_name": "No file uploaded",
            "signals": [],
        }

    name = file_meta["name"].lower()
    size = file_meta["size_bytes"]
    content_type = file_meta.get("content_type", "")
    score = 10
    signals = []

    if any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        score += 15
        signals.append("Image/screenshot uploaded for visual trust analysis.")
    elif any(name.endswith(ext) for ext in [".pdf", ".doc", ".docx"]):
        score += 8
        signals.append("Document-like file uploaded; verify source and metadata.")
    else:
        score += 18
        signals.append("Unusual file type for trust verification.")

    if size < 20_000:
        score += 8
        signals.append("Very small file; may be a compressed screenshot or simple generated asset.")
    if size > 5_000_000:
        score += 5
        signals.append("Large file; manual review recommended before sharing or opening.")

    risky_name_tokens = ["offer", "prize", "claim", "kyc", "verify", "urgent", "payment", "invoice"]
    matched = [token for token in risky_name_tokens if token in name]
    if matched:
        score += min(len(matched) * 9, 24)
        signals.append("Filename contains risk-related words: " + ", ".join(matched))

    if "image" in content_type and not any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        score += 10
        signals.append("Content type and extension do not clearly match.")

    score = max(0, min(score, 100))
    if score >= 70:
        level = "High"
    elif score >= 40:
        level = "Medium"
    else:
        level = "Low"

    return {
        "visual_risk_score": score,
        "visual_risk_level": level,
        "model_name": "TruthShield visual heuristic baseline v1",
        "signals": signals,
    }

