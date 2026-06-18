import base64
import io
import os
from pathlib import Path


DEFAULT_MODEL_ID = "umm-maybe/AI-image-detector"
AI_LABEL_WORDS = ("ai", "artificial", "synthetic", "generated", "fake")
REAL_LABEL_WORDS = ("real", "human", "natural", "authentic")

_classifier = None
_classifier_error = None


def analyze_media_content(file_meta, sample_count=16):
    path = Path(file_meta["path"])
    content_type = file_meta.get("content_type", "")
    is_video = content_type.startswith("video/") or path.suffix.lower() in {
        ".mp4", ".mov", ".webm", ".avi", ".mkv"
    }
    is_image = content_type.startswith("image/") or path.suffix.lower() in {
        ".png", ".jpg", ".jpeg", ".webp"
    }

    if not (is_video or is_image):
        return None

    classifier = _get_classifier()
    if classifier is None:
        return {
            "available": False,
            "detector_mode": "heuristic-fallback",
            "error": _classifier_error,
            "frame_results": [],
        }

    try:
        frames = _sample_video_frames(path, sample_count) if is_video else [_load_image(path)]
        predictions = classifier([frame["image"] for frame in frames])
        if frames and predictions and isinstance(predictions[0], dict):
            predictions = [predictions]

        frame_results = []
        for frame, labels in zip(frames, predictions):
            ai_score = _extract_ai_score(labels)
            frame_results.append({
                "frame_index": frame["frame_index"],
                "timestamp_seconds": frame["timestamp_seconds"],
                "ai_score": round(ai_score * 100, 1),
                "preview": _image_to_data_url(frame["image"]),
            })

        scores = [item["ai_score"] / 100 for item in frame_results]
        average = sum(scores) / max(len(scores), 1)
        suspicious_ratio = sum(score >= 0.70 for score in scores) / max(len(scores), 1)
        final_score = ((average * 0.70) + (suspicious_ratio * 0.30)) * 100

        suspicious_frames = sorted(
            frame_results,
            key=lambda item: item["ai_score"],
            reverse=True,
        )[:6]

        return {
            "available": True,
            "detector_mode": "frame-classifier",
            "model_name": os.getenv("TRUTHSHIELD_AI_MODEL", DEFAULT_MODEL_ID),
            "sampled_frames": len(frame_results),
            "average_frame_score": round(average * 100, 1),
            "suspicious_frame_ratio": round(suspicious_ratio * 100, 1),
            "content_score": round(final_score, 1),
            "frame_results": suspicious_frames,
        }
    except Exception as exc:
        return {
            "available": False,
            "detector_mode": "heuristic-fallback",
            "error": f"Content model could not analyze this file: {exc}",
            "frame_results": [],
        }


def _get_classifier():
    global _classifier, _classifier_error
    if _classifier is not None:
        return _classifier
    if _classifier_error is not None:
        return None

    try:
        from transformers import pipeline

        model_id = os.getenv("TRUTHSHIELD_AI_MODEL", DEFAULT_MODEL_ID)
        _classifier = pipeline("image-classification", model=model_id)
        return _classifier
    except Exception as exc:
        _classifier_error = (
            "Install requirements-ai.txt and restart TruthShield. "
            f"Model loading detail: {exc}"
        )
        return None


def _sample_video_frames(path, sample_count):
    import cv2
    from PIL import Image

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("OpenCV could not open the uploaded video")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 1.0
    if frame_count <= 0:
        capture.release()
        raise ValueError("Video contains no readable frames")

    start = int(frame_count * 0.05)
    end = max(start, int(frame_count * 0.95) - 1)
    indexes = _uniform_indexes(start, end, min(sample_count, frame_count))
    frames = []

    for frame_index in indexes:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append({
            "image": Image.fromarray(rgb),
            "frame_index": frame_index,
            "timestamp_seconds": round(frame_index / fps, 2),
        })

    capture.release()
    if not frames:
        raise ValueError("No frames could be sampled from the video")
    return frames


def _load_image(path):
    from PIL import Image

    image = Image.open(path).convert("RGB")
    return {
        "image": image,
        "frame_index": 0,
        "timestamp_seconds": 0,
    }


def _uniform_indexes(start, end, count):
    if count <= 1 or start >= end:
        return [start]
    step = (end - start) / (count - 1)
    return sorted({round(start + step * index) for index in range(count)})


def _extract_ai_score(labels):
    normalized = [(str(item.get("label", "")).lower(), float(item.get("score", 0))) for item in labels]
    ai_scores = [score for label, score in normalized if any(word in label for word in AI_LABEL_WORDS)]
    if ai_scores:
        return max(ai_scores)

    real_scores = [score for label, score in normalized if any(word in label for word in REAL_LABEL_WORDS)]
    if real_scores:
        return 1 - max(real_scores)

    raise ValueError(f"Unsupported classifier labels: {[label for label, _ in normalized]}")


def _image_to_data_url(image):
    preview = image.copy()
    preview.thumbnail((360, 220))
    buffer = io.BytesIO()
    preview.save(buffer, format="JPEG", quality=72, optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"

