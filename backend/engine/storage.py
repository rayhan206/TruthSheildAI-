from datetime import datetime
import json


def create_scan_workspace(root):
    scans_root = root / "storage" / "scans"
    scans_root.mkdir(parents=True, exist_ok=True)
    scan_id = datetime.utcnow().strftime("scan_%Y%m%d_%H%M%S_%f")
    scan_dir = scans_root / scan_id
    scan_dir.mkdir(parents=True, exist_ok=False)
    return scan_dir, scan_id


def list_scans(root):
    scans_root = root / "storage" / "scans"
    scans_root.mkdir(parents=True, exist_ok=True)
    scans = []
    for scan_dir in sorted(scans_root.iterdir(), reverse=True):
        scan_json = scan_dir / "scan.json"
        if not scan_json.exists():
            continue
        data = json.loads(scan_json.read_text(encoding="utf-8"))
        scans.append({
            "scan_id": data["scan_id"],
            "risk_level": data["ml_result"]["risk_level"],
            "risk_score": data["ml_result"]["risk_score"],
            "visual_risk_level": data["dl_result"]["visual_risk_level"],
        })
    return scans


def read_scan(root, scan_id):
    scan_json = root / "storage" / "scans" / scan_id / "scan.json"
    if not scan_json.exists():
        return None
    return json.loads(scan_json.read_text(encoding="utf-8"))

