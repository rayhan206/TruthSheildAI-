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
    video_exts = [".mp4", ".mov", ".webm", ".avi", ".mkv"]
    image_exts = [".png", ".jpg", ".jpeg", ".webp"]

    if any(name.endswith(ext) for ext in video_exts) or content_type.startswith("video/"):
        score += 24
        signals.append("Video uploaded for AI-media/deepfake-style screening.")
        signals.append("MVP detector checks metadata and naming signals; production upgrade should analyze frames and audio sync.")
    elif any(name.endswith(ext) for ext in image_exts):
        score += 15
        signals.append("Image/screenshot uploaded for visual trust and AI-media screening.")
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

    risky_name_tokens = [
        "offer", "prize", "claim", "kyc", "verify", "urgent", "payment", "invoice",
        "deepfake", "ai", "synthetic", "clone", "celebrity", "crypto", "investment",
    ]
    matched = [token for token in risky_name_tokens if token in name]
    if matched:
        score += min(len(matched) * 9, 24)
        signals.append("Filename contains risk-related words: " + ", ".join(matched))

    if any(token in name for token in ["face", "voice", "clone", "celebrity", "investment"]):
        score += 16
        signals.append("Media filename suggests impersonation, voice/face cloning, or investment persuasion context.")

    if "image" in content_type and not any(name.endswith(ext) for ext in image_exts):
        score += 10
        signals.append("Content type and extension do not clearly match.")
    if "video" in content_type and not any(name.endswith(ext) for ext in video_exts):
        score += 10
        signals.append("Video content type and extension do not clearly match.")

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
