from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import base64
import json
import mimetypes
import sys
import traceback
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(ROOT / "backend"))

from engine.dl_model import analyze_uploaded_file
from engine.feature_extractor import extract_text_features
from engine.ml_model import score_text_risk
from engine.rag_engine import retrieve_context
from engine.report_generator import build_report
from engine.storage import create_scan_workspace, list_scans, read_scan


class TruthShieldHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"status": "ok", "service": "TruthShield Lite"})
        if parsed.path == "/api/scans":
            return self.send_json({"scans": list_scans(ROOT)})
        if parsed.path.startswith("/api/scans/"):
            scan_id = parsed.path.split("/")[-1]
            data = read_scan(ROOT, scan_id)
            if not data:
                return self.send_json({"error": "Scan not found"}, status=404)
            return self.send_json(data)
        return self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/scan":
            return self.send_json({"error": "Route not found"}, status=404)

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw or "{}")

            input_text = payload.get("text", "").strip()
            uploaded_file = payload.get("file")
            scan_dir, scan_id = create_scan_workspace(ROOT)

            file_bytes = None
            file_meta = None
            if uploaded_file and uploaded_file.get("data"):
                filename = uploaded_file.get("name", "upload.bin")
                file_bytes = base64.b64decode(uploaded_file["data"])
                upload_path = scan_dir / filename
                upload_path.write_bytes(file_bytes)
                file_meta = {
                    "name": filename,
                    "size_bytes": len(file_bytes),
                    "path": str(upload_path),
                    "content_type": uploaded_file.get("type", "application/octet-stream"),
                }

            features = extract_text_features(input_text)
            ml_result = score_text_risk(features)
            dl_result = analyze_uploaded_file(file_meta, file_bytes)
            rag_context = retrieve_context(ROOT, input_text, features)
            report = build_report(
                scan_id=scan_id,
                input_text=input_text,
                features=features,
                ml_result=ml_result,
                dl_result=dl_result,
                rag_context=rag_context,
                file_meta=file_meta,
            )

            artifacts = {
                "scan_id": scan_id,
                "input_text": input_text,
                "file": file_meta,
                "features": features,
                "ml_result": ml_result,
                "dl_result": dl_result,
                "rag_context": rag_context,
                "report_markdown": report,
            }

            (scan_dir / "input.txt").write_text(input_text, encoding="utf-8")
            (scan_dir / "features.json").write_text(json.dumps(features, indent=2), encoding="utf-8")
            (scan_dir / "ml_result.json").write_text(json.dumps(ml_result, indent=2), encoding="utf-8")
            (scan_dir / "dl_result.json").write_text(json.dumps(dl_result, indent=2), encoding="utf-8")
            (scan_dir / "rag_context.json").write_text(json.dumps(rag_context, indent=2), encoding="utf-8")
            (scan_dir / "final_report.md").write_text(report, encoding="utf-8")
            (scan_dir / "scan.json").write_text(json.dumps(artifacts, indent=2), encoding="utf-8")

            return self.send_json(artifacts)
        except Exception as exc:
            traceback.print_exc()
            return self.send_json({"error": str(exc)}, status=500)

    def serve_static(self, request_path):
        if request_path in ("", "/"):
            file_path = FRONTEND / "index.html"
        else:
            file_path = (FRONTEND / request_path.lstrip("/")).resolve()
            if FRONTEND not in file_path.parents and file_path != FRONTEND:
                return self.send_json({"error": "Forbidden"}, status=403)

        if not file_path.exists() or not file_path.is_file():
            return self.send_json({"error": "Not found"}, status=404)

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    storage = ROOT / "storage" / "scans"
    storage.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("localhost", 8000), TruthShieldHandler)
    print("TruthShield Lite running at http://localhost:8000")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()

