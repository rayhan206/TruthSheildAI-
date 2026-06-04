# Runbook

## Requirements

- Python 3.10 or newer
- No external packages required for the starter version

## Start The App

From the project root:

```powershell
python -B run_server.py
```

Then open:

```txt
http://localhost:8000
```

The `-B` flag prevents Python from creating `__pycache__` folders, which keeps the workspace cleaner on restricted Windows environments.

## Start The Single-File Edition

For a one-file demo:

```powershell
python -B truthshield_compiled.py
```

This file contains the UI, API server, scanner logic, local knowledge base, and Markdown report generator in exact execution order.

## Test Input

Paste this sample:

```txt
Congratulations! You are selected for a remote job salary 90000. Pay Rs 2999 processing fee today only. Verify at http://verify-job.xyz
```

Expected result:

- High text risk
- Reasons involving urgency, payment, and suspicious URL
- A generated Markdown safety report

## API Endpoints

```txt
GET  /api/health
GET  /api/scans
GET  /api/scans/{scan_id}
POST /api/scan
```
