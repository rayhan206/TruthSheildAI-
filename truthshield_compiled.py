"""
TruthShield Lite - single-file runnable edition.

Run:
    python -B truthshield_compiled.py

Open:
    http://localhost:8000

This file intentionally bundles the frontend, backend routes, scanner logic,
local knowledge base, and report generator into one file for simple demos.
The organized production-style source still lives in backend/, frontend/,
knowledge_base/, and docs/.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
import base64
import json
import mimetypes
import re
import traceback


ROOT = Path(__file__).resolve().parent
SCANS_ROOT = ROOT / "storage" / "scans"

try:
    from backend.engine.media_detector import analyze_media_content
except ImportError:
    analyze_media_content = None


SCAM_PATTERNS = [
    {
        "title": "Advance fee or fake job scam",
        "description": "A fake opportunity asks the victim to pay a registration, processing, training, verification, or equipment fee before receiving salary or benefits.",
        "signals": ["payment before work", "unrealistic salary", "no interview", "urgent joining", "registration fee"],
        "recommended_action": "Do not pay. Verify the company domain, recruiter identity, and official career page.",
    },
    {
        "title": "Phishing link verification scam",
        "description": "The message pressures the user to open a link and verify account, KYC, bank, delivery, or login information.",
        "signals": ["verify now", "account suspended", "login link", "KYC update", "bank warning"],
        "recommended_action": "Avoid the link. Visit the official website manually or call the official support number.",
    },
    {
        "title": "Prize or lottery scam",
        "description": "The sender claims the user won a prize, refund, gift, or lottery and asks for personal information, payment, or a link click.",
        "signals": ["congratulations", "claim prize", "processing fee", "limited time", "tax payment"],
        "recommended_action": "Treat unexpected winnings as suspicious and verify with the official organizer.",
    },
    {
        "title": "Impersonation and authority pressure",
        "description": "The sender pretends to be a government office, police, bank, company, or senior person and pressures immediate action.",
        "signals": ["official warning", "legal action", "blocked account", "confidential request", "do not share"],
        "recommended_action": "Pause and verify through a separate trusted channel before responding.",
    },
    {
        "title": "Suspicious attachment or screenshot",
        "description": "Scammers may send fake invoices, offer letters, screenshots, or documents to create false trust.",
        "signals": ["invoice attachment", "offer letter", "payment proof", "edited screenshot", "unknown file"],
        "recommended_action": "Do not open unknown files on a primary device. Verify source and scan attachments first.",
    },
]


HTML = r"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>TruthShield Lite</title>
    <style>
:root {
  color-scheme: light;
  --color-bg: #f4f7fb;
  --color-surface: #ffffff;
  --color-surface-soft: #f8fbff;
  --color-ink: #0f172a;
  --color-muted: #64748b;
  --color-border: #d8e2f0;
  --color-primary: #155eef;
  --color-primary-dark: #0f46b8;
  --color-primary-soft: #eaf1ff;
  --color-accent: #00a88e;
  --color-accent-soft: #e6fbf6;
  --color-danger: #b42318;
  --color-danger-soft: #fff1f0;
  --color-warning: #b54708;
  --color-warning-soft: #fff7ed;
  --color-safe: #157f3b;
  --color-safe-soft: #ecfdf3;
  --color-purple: #6941c6;
  --color-purple-soft: #f4f0ff;
  --color-code: #0b1220;
  --shadow-sm: 0 10px 30px rgba(15, 23, 42, 0.08);
  --shadow-md: 0 24px 70px rgba(15, 23, 42, 0.12);
  --radius: 8px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
textarea,
input {
  font: inherit;
}

.site-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(135deg, rgba(21, 94, 239, 0.1), transparent 32%),
    linear-gradient(225deg, rgba(0, 168, 142, 0.1), transparent 34%),
    linear-gradient(0deg, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0.76));
}

.app-shell {
  width: min(1220px, calc(100% - 32px));
  margin: 0 auto;
  padding: 24px 0 44px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  margin-bottom: 42px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: var(--radius);
  background: var(--color-ink);
  color: white;
  font-weight: 900;
}

.brand strong,
.brand small {
  display: block;
}

.brand small {
  color: var(--color-muted);
  margin-top: 2px;
}

.nav-links {
  display: flex;
  gap: 8px;
  padding: 6px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-sm);
}

.nav-links a {
  color: var(--color-muted);
  font-weight: 760;
  padding: 9px 12px;
  border-radius: var(--radius);
}

.nav-links a:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 350px;
  gap: 28px;
  align-items: stretch;
  padding: 12px 0 22px;
}

.hero-copy {
  padding: 8px 0;
}

.eyebrow,
.section-kicker {
  display: block;
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 850;
  text-transform: uppercase;
  margin-bottom: 7px;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 12px;
  font-size: clamp(2.4rem, 6vw, 5.4rem);
  line-height: 0.96;
  letter-spacing: 0;
}

h2 {
  margin-bottom: 8px;
}

h3 {
  margin: 20px 0 10px;
}

.lede {
  max-width: 740px;
  color: var(--color-muted);
  font-size: 1.08rem;
  line-height: 1.65;
  margin-bottom: 0;
}

.hero-actions,
.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.primary-link,
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: var(--radius);
  background: var(--color-primary);
  color: white;
  font-weight: 850;
  min-height: 46px;
  padding: 0 18px;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(21, 94, 239, 0.18);
}

.primary-link:hover,
button:hover {
  background: var(--color-primary-dark);
}

.ghost-button,
.secondary-button {
  background: var(--color-surface);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  box-shadow: none;
}

.ghost-button:hover,
.secondary-button:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.hero-card,
.panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-sm);
}

.hero-card {
  padding: 18px;
  box-shadow: var(--shadow-md);
}

.status-pill,
.risk-badge {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--color-border);
  background: var(--color-primary-soft);
  color: var(--color-primary);
  padding: 9px 12px;
  border-radius: var(--radius);
  font-weight: 760;
  white-space: nowrap;
}

.threat-meter {
  height: 10px;
  margin: 18px 0;
  border-radius: 999px;
  background: #e8eef7;
  overflow: hidden;
}

.threat-meter span {
  display: block;
  height: 100%;
  width: var(--meter);
  background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
}

.system-metrics {
  display: grid;
  gap: 10px;
  margin: 0;
}

.system-metrics div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  background: var(--color-surface-soft);
}

.system-metrics dt,
.system-metrics dd {
  margin: 0;
}

.system-metrics dt {
  color: var(--color-muted);
}

.system-metrics dd {
  font-weight: 850;
}

.capability-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 2px 0 18px;
}

.capability-grid article {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.78);
  padding: 16px;
}

.capability-grid span {
  color: var(--color-primary);
  font-weight: 900;
  font-size: 0.8rem;
}

.capability-grid strong {
  display: block;
  margin: 8px 0 6px;
}

.capability-grid p {
  color: var(--color-muted);
  line-height: 1.48;
  margin-bottom: 0;
}

.lab-grid,
.results-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.72fr);
  gap: 18px;
  align-items: start;
  margin-top: 18px;
}

.panel {
  padding: 22px;
}

.panel-heading {
  margin-bottom: 18px;
}

.panel-heading p {
  color: var(--color-muted);
  line-height: 1.55;
  margin-bottom: 0;
}

.mode-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.mode-tab {
  min-height: 42px;
  padding: 0 10px;
  background: var(--color-surface-soft);
  color: var(--color-muted);
  border: 1px solid var(--color-border);
  box-shadow: none;
}

.mode-tab.active {
  background: var(--color-ink);
  color: white;
  border-color: var(--color-ink);
}

.mode-note {
  color: var(--color-muted);
  background: var(--color-primary-soft);
  border: 1px solid #cadbff;
  border-radius: var(--radius);
  padding: 12px;
  line-height: 1.45;
  margin-bottom: 18px;
}

label {
  display: block;
  font-weight: 760;
  margin-bottom: 8px;
}

textarea {
  width: 100%;
  min-height: 245px;
  resize: vertical;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 14px;
  line-height: 1.5;
  color: var(--color-ink);
  margin-bottom: 18px;
  background: var(--color-surface-soft);
  outline: none;
}

textarea:focus,
input[type="file"]:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(21, 94, 239, 0.12);
}

input[type="file"] {
  width: 100%;
  border: 0;
  padding: 0;
  background: transparent;
}

.file-control {
  display: grid;
  gap: 10px;
  border: 1px dashed #9fb2ce;
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 18px;
  background: var(--color-surface-soft);
}

.file-control span {
  color: var(--color-muted);
  font-size: 0.92rem;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.side-panel {
  position: sticky;
  top: 16px;
}

.watchlist {
  display: grid;
  gap: 10px;
}

.watchlist button,
.history-item {
  justify-content: space-between;
  min-height: auto;
  padding: 13px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-soft);
  color: var(--color-ink);
  box-shadow: none;
}

.watchlist button:hover,
.history-item:hover {
  background: var(--color-primary-soft);
}

.mini-guide {
  margin-top: 18px;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--color-purple-soft);
}

.mini-guide h3 {
  margin-top: 0;
}

.mini-guide p {
  color: var(--color-muted);
  line-height: 1.5;
  margin-bottom: 0;
}

.result-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 22px;
}

.score-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 14px;
  background: var(--color-surface-soft);
}

.label {
  display: block;
  color: var(--color-muted);
  font-size: 0.9rem;
  margin-bottom: 6px;
}

.score-card strong {
  font-size: 1.45rem;
}

.category-grid {
  display: grid;
  gap: 10px;
}

.assessment-summary {
  display: grid;
  gap: 7px;
  margin: 4px 0 22px;
  padding: 16px;
  border: 1px solid #cadbff;
  border-left: 4px solid var(--color-primary);
  border-radius: var(--radius);
  background: var(--color-primary-soft);
}

.assessment-summary p {
  margin: 0;
  color: #344054;
  line-height: 1.48;
}

.assessment-summary .section-kicker {
  margin-bottom: 2px;
}

.category-card {
  display: grid;
  gap: 8px;
  padding: 12px;
  border-radius: var(--radius);
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
}

.category-card div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.category-card span {
  color: var(--color-muted);
  font-weight: 760;
}

meter {
  width: 100%;
  height: 10px;
}

.evidence-list {
  padding-left: 18px;
  color: #344054;
  line-height: 1.55;
}

.frame-section {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border);
}

.frame-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.frame-heading h3 {
  margin: 0;
}

.frame-heading span {
  color: var(--color-muted);
  font-size: 0.88rem;
}

.frame-gallery {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.frame-card {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-soft);
}

.frame-card img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  background: var(--color-code);
}

.frame-card div {
  display: grid;
  gap: 3px;
  padding: 9px;
}

.frame-card strong {
  color: var(--color-danger);
  font-size: 0.83rem;
}

.frame-card span {
  color: var(--color-muted);
  font-size: 0.78rem;
}

.highlight-box {
  min-height: 170px;
  max-height: 360px;
  overflow: auto;
  white-space: pre-wrap;
  line-height: 1.7;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface-soft);
  padding: 14px;
  color: #344054;
}

mark {
  border-radius: 5px;
  padding: 1px 4px;
}

.mark-urgency {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.mark-money {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.mark-link {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.mark-trust {
  background: var(--color-purple-soft);
  color: var(--color-purple);
}

.context-list {
  display: grid;
  gap: 10px;
}

.context-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 12px;
  background: var(--color-surface-soft);
}

.context-card h4 {
  margin: 0 0 6px;
}

.context-card p,
.context-card small {
  display: block;
  color: var(--color-muted);
  line-height: 1.45;
}

.history-panel,
.report-panel {
  margin-top: 18px;
}

.history-list {
  display: grid;
  gap: 10px;
}

.history-item {
  width: 100%;
  text-align: left;
}

.history-item span,
.history-item strong,
.history-item small {
  display: block;
}

.history-item small {
  color: var(--color-muted);
  margin-top: 3px;
}

pre {
  margin: 0;
  overflow: auto;
  max-height: 420px;
  white-space: pre-wrap;
  line-height: 1.55;
  background: var(--color-code);
  color: #e4e7ec;
  border-radius: var(--radius);
  padding: 16px;
}

.empty-state {
  color: var(--color-muted);
  margin: 0;
}

.muted {
  color: var(--color-muted);
  background: #f2f4f7;
}

.high {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.medium {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.low {
  color: var(--color-safe);
  background: var(--color-safe-soft);
}

@media (max-width: 980px) {
  .hero,
  .lab-grid,
  .results-layout,
  .capability-grid {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
  }
}

@media (max-width: 700px) {
  .app-shell {
    width: min(100% - 24px, 1220px);
    padding-top: 18px;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
    margin-bottom: 28px;
  }

  .nav-links,
  .mode-tabs,
  .score-grid {
    grid-template-columns: 1fr 1fr;
    width: 100%;
  }

  .nav-links {
    display: grid;
  }

  h1 {
    font-size: 2.8rem;
  }

  .frame-gallery {
    grid-template-columns: 1fr 1fr;
  }
}

    </style>
  </head>
  <body>
    <div class="site-bg" aria-hidden="true"></div>
    <main class="app-shell">
      <header class="topbar">
        <a class="brand" href="/">
          <span class="brand-mark">TS</span>
          <span>
            <strong>TruthShield</strong>
            <small>AI risk intelligence</small>
          </span>
        </a>
        <nav class="nav-links" aria-label="Primary">
          <a href="#lab">Lab</a>
          <a href="#results">Results</a>
          <a href="#history">History</a>
          <a href="#report">Report</a>
        </nav>
      </header>

      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Digital forensics lab</p>
          <h1>Verify before you trust.</h1>
          <p class="lede">
            Analyze scam messages, fake job offers, phishing links, suspicious documents, and AI-generated media in one privacy-first workspace.
          </p>
          <div class="hero-actions">
            <a class="primary-link" href="#lab">Open scanner</a>
            <button class="ghost-button" id="sampleButton" type="button">Load scam sample</button>
          </div>
        </div>
        <aside class="hero-card" id="system">
          <div class="status-pill" id="healthStatus">Checking backend...</div>
          <div class="threat-meter" aria-label="Threat intelligence readiness">
            <span style="--meter: 82%"></span>
          </div>
          <dl class="system-metrics">
            <div>
              <dt>Storage</dt>
              <dd>Local-first</dd>
            </div>
            <div>
              <dt>AI Media</dt>
              <dd>Detector MVP</dd>
            </div>
            <div>
              <dt>Reports</dt>
              <dd>Export-ready</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section class="capability-grid" aria-label="Capabilities">
        <article>
          <span>01</span>
          <strong>Message intelligence</strong>
          <p>Pressure, payment, impersonation, and suspicious wording signals.</p>
        </article>
        <article>
          <span>02</span>
          <strong>URL risk scan</strong>
          <p>Fake login paths, risky domains, shortened links, and brand mismatch hints.</p>
        </article>
        <article>
          <span>03</span>
          <strong>AI media detector</strong>
          <p>Image/video metadata and deepfake-style filename signal analysis.</p>
        </article>
        <article>
          <span>04</span>
          <strong>Evidence report</strong>
          <p>Markdown artifact with reasons, context, and safe next steps.</p>
        </article>
      </section>

      <section class="lab-grid" id="lab">
        <form id="scanForm" class="panel scan-panel">
          <div class="panel-heading">
            <span class="section-kicker">Scanner</span>
            <h2>Choose investigation mode</h2>
            <p>Each mode tunes the interface for a specific threat type. The backend stays local and database-free.</p>
          </div>

          <div class="mode-tabs" role="tablist" aria-label="Scan modes">
            <button class="mode-tab active" type="button" data-mode="message">Scam Text</button>
            <button class="mode-tab" type="button" data-mode="job">Fake Job</button>
            <button class="mode-tab" type="button" data-mode="url">URL</button>
            <button class="mode-tab" type="button" data-mode="media">AI Media</button>
          </div>

          <div class="mode-note" id="modeNote">
            Paste suspicious text, email, SMS, or WhatsApp content.
          </div>

          <label for="textInput">Evidence text</label>
          <textarea id="textInput" placeholder="Paste suspicious content here..."></textarea>

          <label for="fileInput">Optional screenshot, document, image, or video</label>
          <div class="file-control">
            <input id="fileInput" type="file" accept="image/*,video/*,.pdf,.doc,.docx,.txt" />
            <span id="fileName">No file selected</span>
          </div>

          <div class="form-actions">
            <button type="submit" id="scanButton">Run investigation</button>
            <button type="button" class="secondary-button" id="clearButton">Clear</button>
          </div>
        </form>

        <aside class="panel side-panel">
          <div class="panel-heading">
            <span class="section-kicker">Threat library</span>
            <h2>Watchlist</h2>
          </div>
          <div class="watchlist">
            <button type="button" data-template="kyc">KYC phishing</button>
            <button type="button" data-template="job">Processing-fee job</button>
            <button type="button" data-template="prize">Prize claim scam</button>
            <button type="button" data-template="media">Deepfake video check</button>
          </div>
          <div class="mini-guide">
            <h3>AI Detector scope</h3>
            <p>
              This MVP checks media metadata and suspicious naming patterns. A production upgrade would add frame extraction, face artifacts, audio sync, and a trained deepfake classifier.
            </p>
          </div>
        </aside>
      </section>

      <section class="results-layout" id="results">
        <section class="panel result-panel">
          <div class="result-header">
            <div>
              <span class="section-kicker">Verdict</span>
              <h2>Risk report</h2>
            </div>
            <span id="riskBadge" class="risk-badge muted">Waiting</span>
          </div>

          <div class="score-grid">
            <div class="score-card">
              <span class="label">Scam/Text Risk</span>
              <strong id="textScore">--</strong>
            </div>
            <div class="score-card">
              <span class="label">Media/File Risk</span>
              <strong id="fileScore">--</strong>
            </div>
            <div class="score-card">
              <span class="label">Investigation Mode</span>
              <strong id="modeScore">--</strong>
            </div>
          </div>

          <div id="assessmentSummary" class="assessment-summary">
            <span class="section-kicker">Assessment summary</span>
            <p>Run a scan to generate a plain-English assessment.</p>
          </div>

          <h3>Risk categories</h3>
          <div id="categoryGrid" class="category-grid">
            <p class="empty-state">Run a scan to populate category meters.</p>
          </div>

          <h3>Evidence</h3>
          <ul id="evidenceList" class="evidence-list">
            <li>Run a scan to see evidence.</li>
          </ul>

          <div class="frame-section" id="frameSection" hidden>
            <div class="frame-heading">
              <h3>Most suspicious frames</h3>
              <span id="frameSummary"></span>
            </div>
            <div id="frameGallery" class="frame-gallery"></div>
          </div>
        </section>

        <section class="panel evidence-panel">
          <div class="panel-heading">
            <span class="section-kicker">Highlighted evidence</span>
            <h2>Signal map</h2>
          </div>
          <div id="highlightedText" class="highlight-box">Risky phrases, links, and money terms will be highlighted here.</div>

          <h3>Recommended safety context</h3>
          <div id="contextList" class="context-list"></div>
        </section>
      </section>

      <section class="panel history-panel" id="history">
        <div class="result-header">
          <div>
            <span class="section-kicker">Local history</span>
            <h2>Recent scans</h2>
          </div>
          <button id="refreshHistory" class="secondary-button" type="button">Refresh</button>
        </div>
        <div id="historyList" class="history-list">
          <p class="empty-state">No scans loaded yet.</p>
        </div>
      </section>

      <section class="panel report-panel" id="report">
        <div class="result-header">
          <div>
            <span class="section-kicker">Artifact</span>
            <h2>Generated Markdown report</h2>
          </div>
          <button id="copyReport" class="secondary-button" type="button">Copy</button>
        </div>
        <pre id="markdownReport">No report yet.</pre>
      </section>
    </main>

    <script>
const form = document.querySelector("#scanForm");
const textInput = document.querySelector("#textInput");
const fileInput = document.querySelector("#fileInput");
const scanButton = document.querySelector("#scanButton");
const healthStatus = document.querySelector("#healthStatus");
const riskBadge = document.querySelector("#riskBadge");
const textScore = document.querySelector("#textScore");
const fileScore = document.querySelector("#fileScore");
const modeScore = document.querySelector("#modeScore");
const evidenceList = document.querySelector("#evidenceList");
const contextList = document.querySelector("#contextList");
const markdownReport = document.querySelector("#markdownReport");
const copyReport = document.querySelector("#copyReport");
const sampleButton = document.querySelector("#sampleButton");
const clearButton = document.querySelector("#clearButton");
const fileName = document.querySelector("#fileName");
const modeNote = document.querySelector("#modeNote");
const modeTabs = document.querySelectorAll(".mode-tab");
const categoryGrid = document.querySelector("#categoryGrid");
const highlightedText = document.querySelector("#highlightedText");
const historyList = document.querySelector("#historyList");
const refreshHistory = document.querySelector("#refreshHistory");
const watchlistButtons = document.querySelectorAll(".watchlist button");
const frameSection = document.querySelector("#frameSection");
const frameGallery = document.querySelector("#frameGallery");
const frameSummary = document.querySelector("#frameSummary");
const assessmentSummary = document.querySelector("#assessmentSummary");

let activeMode = "message";

const samples = {
  message: `Your bank account is suspended. Verify now at http://login-bank-support.xyz and pay Rs 499 to avoid final blocking.`,
  job: `Congratulations! You are selected for a remote data analyst job with salary 90000 per month.

To confirm your joining, pay Rs 2999 processing fee today only and verify your profile at http://verify-job.xyz.

This offer is confidential and no interview is required.`,
  url: `Claim your refund now: https://sbi-verify-login.xyz/free/refund. This link expires today only.`,
  media: `AI media detector mode: upload a video or image and add any context here. Example: "This celebrity investment video asks me to pay crypto today."`,
  kyc: `Your KYC is expired. Account will be blocked today. Verify now at http://kyc-bank-login.xyz and upload Aadhaar details immediately.`,
  prize: `Congratulations! You won a phone worth Rs 80000. Pay Rs 999 processing fee today only to claim your prize.`,
};

const modeHelp = {
  message: "Paste suspicious text, email, SMS, or WhatsApp content.",
  job: "Paste the offer letter text, recruiter message, salary promise, or payment request.",
  url: "Paste the full URL or message containing the link. Add claimed brand context if known.",
  media: "Upload an image or video. Add context such as who appears, what is claimed, and what action is requested.",
};

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    healthStatus.textContent = data.status === "ok" ? "Backend online" : "Backend unavailable";
  } catch {
    healthStatus.textContent = "Backend unavailable";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  scanButton.disabled = true;
  scanButton.textContent = "Investigating...";

  try {
    const file = fileInput.files[0];
    const modePrefix = `[Mode: ${activeMode.toUpperCase()}]\n`;
    const payload = {
      text: modePrefix + textInput.value,
      file: file ? await fileToPayload(file) : null,
    };

    const response = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Scan failed");
    }

    const result = await response.json();
    renderResult(result);
    loadHistory();
  } catch (error) {
    alert(error.message);
  } finally {
    scanButton.disabled = false;
    scanButton.textContent = "Run investigation";
  }
});

modeTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    activeMode = tab.dataset.mode;
    modeTabs.forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    modeNote.textContent = modeHelp[activeMode];
    modeScore.textContent = labelMode(activeMode);
  });
});

sampleButton.addEventListener("click", () => {
  textInput.value = samples[activeMode] || samples.message;
  textInput.focus();
});

watchlistButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const template = button.dataset.template;
    const nextMode = template === "media" ? "media" : template === "job" ? "job" : "message";
    setMode(nextMode);
    textInput.value = samples[template] || samples.message;
    textInput.focus();
  });
});

clearButton.addEventListener("click", () => {
  textInput.value = "";
  fileInput.value = "";
  fileName.textContent = "No file selected";
  resetResults();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? `${file.name} (${formatBytes(file.size)})` : "No file selected";
  if (file?.type.startsWith("video/") || /\.(mp4|mov|webm|avi|mkv)$/i.test(file?.name || "")) {
    setMode("media");
  }
});

copyReport.addEventListener("click", async () => {
  await navigator.clipboard.writeText(markdownReport.textContent);
  copyReport.textContent = "Copied";
  setTimeout(() => {
    copyReport.textContent = "Copy";
  }, 1200);
});

refreshHistory.addEventListener("click", loadHistory);

function renderResult(result) {
  const mediaMode = isMediaResult(result);
  const mediaScoreValue = result.dl_result.visual_risk_score;
  const level = mediaMode ? mediaVerdict(mediaScoreValue) : result.ml_result.risk_level;
  riskBadge.textContent = mediaMode ? level.label : `${level} Risk`;
  riskBadge.className = `risk-badge ${mediaMode ? level.className : level.toLowerCase()}`;
  textScore.textContent = `${result.ml_result.risk_score}/100`;
  fileScore.textContent = `${result.dl_result.visual_risk_score}/100`;
  modeScore.textContent = labelMode(activeMode);

  renderCategories(result);
  renderAssessment(result, mediaMode);
  renderEvidence(result);
  renderFrames(result.dl_result);
  renderContext(result.rag_context);
  renderHighlightedText(result.input_text, result.features);

  markdownReport.textContent = result.report_markdown;
}

function renderAssessment(result, mediaMode) {
  const features = result.features;
  const mediaScoreValue = result.dl_result.visual_risk_score;
  const textRisk = result.ml_result.risk_level.toLowerCase();
  const mediaStatement = mediaMode
    ? mediaScoreValue >= 70
      ? `TruthShield detects this media as likely AI-generated with a ${mediaScoreValue}/100 likelihood score.`
      : mediaScoreValue >= 40
        ? `TruthShield found uncertain AI-generation signals in this media (${mediaScoreValue}/100).`
        : `TruthShield did not find strong AI-generation signals in this media (${mediaScoreValue}/100).`
    : `TruthShield rated the submitted text as ${textRisk} scam risk (${result.ml_result.risk_score}/100).`;

  const moneyStatement = features.money_terms.length || features.money_mention_count
    ? "Money or payment language was detected and should be checked carefully."
    : "Money and payment risk is low; no strong financial request was detected.";
  const linkStatement = features.suspicious_url_count
    ? "A suspicious link was detected and should not be opened before verification."
    : "Link risk is low; no suspicious URL pattern was detected.";
  const identityStatement = features.trust_terms.length
    ? "Some identity or trust-building language was detected."
    : "Identity and impersonation language risk is low in the submitted context.";

  assessmentSummary.innerHTML = `
    <span class="section-kicker">Assessment summary</span>
    <p><strong>${escapeHtml(mediaStatement)}</strong></p>
    <p>${escapeHtml(moneyStatement)}</p>
    <p>${escapeHtml(linkStatement)}</p>
    <p>${escapeHtml(identityStatement)}</p>
  `;
}

function isMediaResult(result) {
  return activeMode === "media"
    || result.dl_result.detector_mode === "frame-classifier"
    || Boolean(result.dl_result.frame_results?.length)
    || /^\[Mode: MEDIA\]/.test(result.input_text || "");
}

function mediaVerdict(score) {
  if (score >= 70) return { label: "Likely AI-Generated", className: "high" };
  if (score >= 40) return { label: "AI Result Uncertain", className: "medium" };
  return { label: "No Strong AI Signal", className: "low" };
}

function renderFrames(mediaResult) {
  const frames = mediaResult.frame_results || [];
  const analysis = mediaResult.content_analysis || {};
  if (!frames.length) {
    frameSection.hidden = true;
    frameGallery.innerHTML = "";
    return;
  }

  frameSection.hidden = false;
  frameSummary.textContent = `${analysis.sampled_frames || frames.length} sampled`;
  frameGallery.innerHTML = "";
  frames.forEach((frame) => {
    const card = document.createElement("article");
    card.className = "frame-card";
    card.innerHTML = `
      <img src="${frame.preview}" alt="Sampled video frame at ${frame.timestamp_seconds} seconds" />
      <div>
        <strong>${frame.ai_score}% AI likelihood</strong>
        <span>${frame.timestamp_seconds}s</span>
      </div>
    `;
    frameGallery.appendChild(card);
  });
}

function renderCategories(result) {
  const features = result.features;
  const categories = [
    ["Urgency", Math.min(features.urgency_terms.length * 28, 100)],
    ["Money", Math.min((features.money_terms.length + features.money_mention_count) * 24, 100)],
    ["Link", Math.min((features.url_count * 24) + (features.suspicious_url_count * 38), 100)],
    ["Identity", Math.min(features.trust_terms.length * 26, 100)],
    ["Media", result.dl_result.visual_risk_score],
  ];

  categoryGrid.innerHTML = "";
  categories.forEach(([name, value]) => {
    const card = document.createElement("article");
    card.className = "category-card";
    card.innerHTML = `
      <div>
        <strong>${name}</strong>
        <span>${value}/100</span>
      </div>
      <meter min="0" max="100" value="${value}"></meter>
    `;
    categoryGrid.appendChild(card);
  });
}

function renderEvidence(result) {
  evidenceList.innerHTML = "";
  [...result.ml_result.top_reasons, ...result.dl_result.signals].forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    evidenceList.appendChild(li);
  });
}

function renderContext(contexts) {
  contextList.innerHTML = "";
  contexts.forEach((context) => {
    const card = document.createElement("article");
    card.className = "context-card";
    card.innerHTML = `
      <h4>${escapeHtml(context.title)}</h4>
      <p>${escapeHtml(context.description)}</p>
      <small>${escapeHtml(context.recommended_action || "Verify through official channels.")}</small>
    `;
    contextList.appendChild(card);
  });
}

function renderHighlightedText(text, features) {
  const raw = text.replace(/^\[Mode: [A-Z]+\]\n/, "") || "No text submitted.";
  let escaped = escapeHtml(raw);
  const terms = [
    ...features.urgency_terms.map((term) => [term, "mark-urgency"]),
    ...features.money_terms.map((term) => [term, "mark-money"]),
    ...features.trust_terms.map((term) => [term, "mark-trust"]),
    ...features.urls.map((term) => [term, "mark-link"]),
  ];

  terms
    .sort((a, b) => b[0].length - a[0].length)
    .forEach(([term, className]) => {
      if (!term) return;
      const safeTerm = escapeRegExp(escapeHtml(term));
      escaped = escaped.replace(new RegExp(safeTerm, "gi"), (match) => `<mark class="${className}">${match}</mark>`);
    });

  highlightedText.innerHTML = escaped;
}

async function loadHistory() {
  try {
    const response = await fetch("/api/scans");
    const data = await response.json();
    const scans = data.scans || [];
    if (!scans.length) {
      historyList.innerHTML = `<p class="empty-state">No local scans yet.</p>`;
      return;
    }

    historyList.innerHTML = "";
    scans.slice(0, 8).forEach((scan) => {
      const item = document.createElement("button");
      item.className = "history-item";
      item.type = "button";
      item.innerHTML = `
        <span>
          <strong>${scan.scan_id}</strong>
          <small>${scan.visual_risk_level}</small>
        </span>
        <b class="${scan.risk_level.toLowerCase()}">${scan.risk_score}/100</b>
      `;
      item.addEventListener("click", () => openHistory(scan.scan_id));
      historyList.appendChild(item);
    });
  } catch {
    historyList.innerHTML = `<p class="empty-state">Could not load local history.</p>`;
  }
}

async function openHistory(scanId) {
  const response = await fetch(`/api/scans/${scanId}`);
  if (!response.ok) return;
  renderResult(await response.json());
  document.querySelector("#results").scrollIntoView({ behavior: "smooth" });
}

function setMode(mode) {
  activeMode = mode;
  modeTabs.forEach((item) => item.classList.toggle("active", item.dataset.mode === mode));
  modeNote.textContent = modeHelp[mode];
  modeScore.textContent = labelMode(mode);
}

function resetResults() {
  riskBadge.textContent = "Waiting";
  riskBadge.className = "risk-badge muted";
  textScore.textContent = "--";
  fileScore.textContent = "--";
  modeScore.textContent = labelMode(activeMode);
  evidenceList.innerHTML = "<li>Run a scan to see evidence.</li>";
  contextList.innerHTML = "";
  categoryGrid.innerHTML = `<p class="empty-state">Run a scan to populate category meters.</p>`;
  highlightedText.textContent = "Risky phrases, links, and money terms will be highlighted here.";
  assessmentSummary.innerHTML = `
    <span class="section-kicker">Assessment summary</span>
    <p>Run a scan to generate a plain-English assessment.</p>
  `;
  frameSection.hidden = true;
  frameGallery.innerHTML = "";
  markdownReport.textContent = "No report yet.";
}

function fileToPayload(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = String(reader.result).split(",")[1];
      resolve({
        name: file.name,
        type: file.type,
        data: base64,
      });
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function labelMode(mode) {
  return {
    message: "Scam Text",
    job: "Fake Job",
    url: "URL",
    media: "AI Media",
  }[mode] || "Scanner";
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkHealth();
setMode(activeMode);
loadHistory();

    </script>
  </body>
</html>
"""


URGENCY_TERMS = {
    "urgent", "immediately", "limited", "deadline", "final", "warning",
    "verify now", "act now", "today only", "expire", "blocked", "suspended",
}
MONEY_TERMS = {
    "payment", "pay", "fee", "deposit", "crypto", "bitcoin", "upi",
    "bank", "salary", "prize", "lottery", "refund", "investment",
    "registration fee", "processing fee",
}
TRUST_TERMS = {
    "official", "government", "verified", "guaranteed", "no interview",
    "selected", "congratulations", "confidential", "do not share",
}
SUSPICIOUS_TLDS = {".zip", ".mov", ".top", ".xyz", ".click", ".work", ".support"}


def extract_text_features(text):
    normalized = " ".join(text.lower().split())
    urls = re.findall(r"https?://[^\s)>\]]+|www\.[^\s)>\]]+", normalized)
    phones = re.findall(r"(?:\+?\d[\s-]?){8,}", normalized)
    emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", normalized)
    money_mentions = re.findall(r"(?:rs\.?|inr|\$|â‚¹)\s?\d+|\d+\s?(?:rs|inr|rupees|dollars)", normalized)
    uppercase_words = re.findall(r"\b[A-Z]{3,}\b", text)
    suspicious_urls = [url for url in urls if is_suspicious_url(url)]
    words = re.findall(r"\w+", text)

    return {
        "word_count": len(words),
        "url_count": len(urls),
        "urls": urls,
        "suspicious_url_count": len(suspicious_urls),
        "suspicious_urls": suspicious_urls,
        "phone_count": len(phones),
        "email_count": len(emails),
        "money_mention_count": len(money_mentions),
        "money_mentions": money_mentions,
        "exclamation_count": text.count("!"),
        "uppercase_word_count": len(uppercase_words),
        "avg_word_length": round(sum(len(word) for word in words) / max(len(words), 1), 2),
        "urgency_terms": sorted(term for term in URGENCY_TERMS if term in normalized),
        "money_terms": sorted(term for term in MONEY_TERMS if term in normalized),
        "trust_terms": sorted(term for term in TRUST_TERMS if term in normalized),
    }


def is_suspicious_url(url):
    if url.startswith("www."):
        url = "https://" + url
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if any(host.endswith(tld) for tld in SUSPICIOUS_TLDS):
        return True
    if "@" in url or host.count("-") >= 2 or len(host.split(".")[0]) > 25:
        return True
    return any(token in host + path for token in ["login", "verify", "bonus", "claim", "free"])


def score_text_risk(features):
    score = 8
    reasons = []
    weights = {
        "suspicious_url_count": 22,
        "url_count": 6,
        "phone_count": 5,
        "money_mention_count": 14,
        "exclamation_count": 2,
        "uppercase_word_count": 1,
    }

    for key, weight in weights.items():
        score += min(features.get(key, 0) * weight, 28)

    if features["urgency_terms"]:
        score += min(len(features["urgency_terms"]) * 9, 24)
        reasons.append("Uses urgency or pressure language.")
    if features["money_terms"]:
        score += min(len(features["money_terms"]) * 8, 24)
        reasons.append("Mentions payment, money, reward, salary, or banking terms.")
    if features["trust_terms"]:
        score += min(len(features["trust_terms"]) * 5, 15)
        reasons.append("Uses trust-building language commonly found in scams.")
    if features["suspicious_url_count"]:
        reasons.append("Contains one or more suspicious-looking URLs.")
    elif features["url_count"]:
        reasons.append("Contains links that should be verified before clicking.")
    if features["phone_count"]:
        reasons.append("Includes phone numbers, which are common in social-engineering messages.")
    if features["money_mention_count"]:
        reasons.append("Contains explicit money amounts or payment references.")
    if features["word_count"] < 8 and (features["url_count"] or features["phone_count"]):
        score += 10
        reasons.append("Very short message with contact/link payload.")

    score = max(0, min(round(score), 100))
    level = "High" if score >= 75 else "Medium" if score >= 45 else "Low"
    if not reasons:
        reasons.append("No strong scam indicators found in the text, but verification is still recommended.")

    return {
        "risk_score": score,
        "risk_level": level,
        "model_name": "TruthShield heuristic baseline v1",
        "top_reasons": reasons[:6],
    }


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

    matched = [
        token for token in [
            "offer", "prize", "claim", "kyc", "verify", "urgent", "payment", "invoice",
            "deepfake", "ai", "synthetic", "clone", "celebrity", "crypto", "investment",
        ]
        if token in name
    ]
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

    heuristic_score = max(0, min(score, 100))
    content_result = analyze_media_content(file_meta) if analyze_media_content else None

    if content_result and content_result.get("available"):
        score = round((content_result["content_score"] * 0.90) + (heuristic_score * 0.10))
        signals.insert(
            0,
            f"Frame model sampled {content_result['sampled_frames']} frames; "
            f"average AI likelihood was {content_result['average_frame_score']}%.",
        )
        model_name = content_result["model_name"]
    else:
        score = heuristic_score
        model_name = "TruthShield metadata heuristic fallback"
        if content_result:
            signals.insert(0, content_result.get("error", "AI content model is unavailable."))

    level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    return {
        "visual_risk_score": score,
        "visual_risk_level": level,
        "model_name": model_name,
        "detector_mode": content_result.get("detector_mode") if content_result else "heuristic-fallback",
        "content_analysis": content_result,
        "heuristic_score": heuristic_score,
        "frame_results": content_result.get("frame_results", []) if content_result else [],
        "signals": signals,
    }


def retrieve_context(text, features, limit=3):
    query_terms = set(tokens(text))
    query_terms.update(features.get("urgency_terms", []))
    query_terms.update(features.get("money_terms", []))
    query_terms.update(features.get("trust_terms", []))
    scored = []

    for item in SCAM_PATTERNS:
        item_terms = set(tokens(" ".join([item["title"], item["description"], " ".join(item["signals"])])))
        overlap = len(query_terms.intersection(item_terms))
        if features.get("url_count") and "link" in item_terms:
            overlap += 2
        if features.get("money_mention_count") and "payment" in item_terms:
            overlap += 2
        scored.append((overlap, item))

    scored.sort(key=lambda row: row[0], reverse=True)
    results = [
        {**item, "match_score": score}
        for score, item in scored[:limit]
        if score > 0
    ]
    return results or [{
        "title": "General verification",
        "description": "When evidence is limited, verify through official channels before clicking links, paying money, or sharing personal data.",
        "signals": ["Unknown sender", "Unverified request", "External links or attachments"],
        "recommended_action": "Contact the organization through its official website or known phone number.",
        "match_score": 0,
    }]


def tokens(value):
    return re.findall(r"[a-zA-Z]{3,}", value.lower())


def build_report(scan_id, input_text, features, ml_result, dl_result, rag_context, file_meta):
    media_mode = input_text.startswith("[Mode: MEDIA]") or dl_result.get("detector_mode") == "frame-classifier"
    media_score = dl_result.get("visual_risk_score", 0)
    if media_score >= 70:
        media_verdict = "likely AI-generated"
    elif media_score >= 40:
        media_verdict = "uncertain for AI generation"
    else:
        media_verdict = "not showing strong AI-generation signals"

    lines = [
        "# TruthShield Lite Risk Report",
        "",
        f"Scan ID: `{scan_id}`",
        "",
        "## Verdict",
        "",
        f"- Text risk: **{ml_result['risk_level']}** ({ml_result['risk_score']}/100)",
        f"- Visual/file risk: **{dl_result['visual_risk_level']}** ({dl_result['visual_risk_score']}/100)",
        f"- Media detector: `{dl_result.get('detector_mode', 'not-applicable')}`",
        f"- Media model: `{dl_result.get('model_name', 'Not analyzed')}`",
        "",
        "## Quick Assessment",
        "",
        (
            f"- TruthShield detects the uploaded media as **{media_verdict}** ({media_score}/100)."
            if media_mode else
            f"- TruthShield rated the submitted text as **{ml_result['risk_level']} scam risk** ({ml_result['risk_score']}/100)."
        ),
        f"- Money/payment risk is {'present' if features['money_terms'] or features['money_mention_count'] else 'low'}.",
        f"- Link risk is {'present' if features['suspicious_url_count'] else 'low'}.",
        f"- Identity/impersonation language risk is {'present' if features['trust_terms'] else 'low'}.",
        "",
        "## Key Reasons",
        "",
    ]

    for reason in ml_result["top_reasons"]:
        lines.append(f"- {reason}")
    for signal in dl_result["signals"]:
        lines.append(f"- {signal}")

    content_analysis = dl_result.get("content_analysis") or {}
    if content_analysis.get("available"):
        lines.extend([
            "",
            "## Frame Analysis",
            "",
            f"- Sampled frames: {content_analysis['sampled_frames']}",
            f"- Average frame AI likelihood: {content_analysis['average_frame_score']}%",
            f"- Suspicious frame ratio: {content_analysis['suspicious_frame_ratio']}%",
        ])

    lines.extend([
        "",
        "## Extracted Signals",
        "",
        f"- URLs found: {features['url_count']}",
        f"- Suspicious URLs: {features['suspicious_url_count']}",
        f"- Phone numbers: {features['phone_count']}",
        f"- Money mentions: {features['money_mention_count']}",
        f"- Urgency terms: {', '.join(features['urgency_terms']) or 'None'}",
        f"- Money terms: {', '.join(features['money_terms']) or 'None'}",
        "",
        "## Retrieved Safety Context",
        "",
    ])

    for context in rag_context:
        lines.extend([f"### {context['title']}", context["description"], "", "Signals:"])
        for signal in context["signals"]:
            lines.append(f"- {signal}")
        lines.extend(["", f"Recommended action: {context['recommended_action']}", ""])

    if file_meta:
        lines.extend([
            "## Uploaded File",
            "",
            f"- Name: `{file_meta['name']}`",
            f"- Size: {file_meta['size_bytes']} bytes",
            "",
        ])

    lines.extend([
        "## Safe Next Steps",
        "",
        "- Do not click links until the sender is verified.",
        "- Do not pay fees or deposits based only on this message.",
        "- Verify through official websites, known phone numbers, or trusted contacts.",
        "- Preserve the evidence if this may need to be reported.",
        "",
        "## Original Text",
        "",
        "```txt",
        input_text or "(No text provided)",
        "```",
    ])
    return "\n".join(lines)


def create_scan_workspace():
    SCANS_ROOT.mkdir(parents=True, exist_ok=True)
    scan_id = datetime.utcnow().strftime("scan_%Y%m%d_%H%M%S_%f")
    scan_dir = SCANS_ROOT / scan_id
    scan_dir.mkdir(parents=True, exist_ok=False)
    return scan_dir, scan_id


def list_scans():
    SCANS_ROOT.mkdir(parents=True, exist_ok=True)
    scans = []
    for scan_dir in sorted(SCANS_ROOT.iterdir(), reverse=True):
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


class TruthShieldCompiledHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"status": "ok", "service": "TruthShield Lite single-file"})
        if parsed.path == "/api/scans":
            return self.send_json({"scans": list_scans()})
        if parsed.path.startswith("/api/scans/"):
            scan_id = parsed.path.split("/")[-1]
            scan_json = SCANS_ROOT / scan_id / "scan.json"
            if not scan_json.exists():
                return self.send_json({"error": "Scan not found"}, status=404)
            return self.send_json(json.loads(scan_json.read_text(encoding="utf-8")))
        return self.serve_index()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/scan":
            return self.send_json({"error": "Route not found"}, status=404)

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8") or "{}")
            input_text = payload.get("text", "").strip()
            uploaded_file = payload.get("file")
            scan_dir, scan_id = create_scan_workspace()

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
            rag_context = retrieve_context(input_text, features)
            report = build_report(scan_id, input_text, features, ml_result, dl_result, rag_context, file_meta)
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

    def serve_index(self):
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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
    SCANS_ROOT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("localhost", 8000), TruthShieldCompiledHandler)
    print("TruthShield Lite single-file edition running at http://localhost:8000")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()




