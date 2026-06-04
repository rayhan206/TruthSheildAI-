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
  --color-bg: #f6f8fc;
  --color-surface: #ffffff;
  --color-surface-soft: #f9fbff;
  --color-ink: #101828;
  --color-muted: #667085;
  --color-border: #d9e2ef;
  --color-primary: #0b5fff;
  --color-primary-dark: #0747b6;
  --color-primary-soft: #eaf1ff;
  --color-accent: #00a88e;
  --color-danger: #b42318;
  --color-warning: #b54708;
  --color-safe: #157f3b;
  --color-code: #0b1220;
  --shadow-sm: 0 10px 30px rgba(16, 24, 40, 0.08);
  --shadow-md: 0 24px 70px rgba(16, 24, 40, 0.12);
  --radius: 8px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body::selection {
  background: var(--color-primary-soft);
}

a {
  color: inherit;
  text-decoration: none;
}

.site-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  background:
    linear-gradient(135deg, rgba(11, 95, 255, 0.08), transparent 34%),
    linear-gradient(225deg, rgba(0, 168, 142, 0.08), transparent 36%);
}

.app-shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 24px 0 40px;
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
  background: rgba(255, 255, 255, 0.74);
  box-shadow: var(--shadow-sm);
}

.nav-links a {
  color: var(--color-muted);
  font-weight: 750;
  padding: 9px 12px;
  border-radius: var(--radius);
}

.nav-links a:hover {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 28px;
  align-items: stretch;
  padding: 12px 0 22px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--color-primary);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.78rem;
  letter-spacing: 0;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 10px;
  font-size: clamp(2rem, 5vw, 4.8rem);
  line-height: 1;
  letter-spacing: 0;
}

.lede {
  max-width: 720px;
  color: var(--color-muted);
  font-size: 1.08rem;
  line-height: 1.6;
  margin-bottom: 0;
}

.hero-actions {
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
  font: inherit;
  font-weight: 850;
  min-height: 46px;
  padding: 0 18px;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(11, 95, 255, 0.18);
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

.hero-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-md);
  padding: 18px;
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
  font-weight: 700;
  white-space: nowrap;
}

.system-metrics {
  display: grid;
  gap: 10px;
  margin: 18px 0 0;
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

.trust-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 0 0 18px;
}

.trust-strip span {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.76);
  color: var(--color-muted);
  font-weight: 800;
  padding: 12px 14px;
  text-align: center;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr);
  gap: 18px;
  align-items: start;
}

.panel {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: 22px;
}

.panel-heading {
  margin-bottom: 18px;
}

.panel-heading h2,
.result-header h2 {
  margin-bottom: 6px;
}

.panel-heading p {
  color: var(--color-muted);
  line-height: 1.55;
  margin-bottom: 0;
}

.section-kicker {
  display: block;
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 850;
  text-transform: uppercase;
  margin-bottom: 6px;
}

label {
  display: block;
  font-weight: 750;
  margin-bottom: 8px;
}

textarea {
  width: 100%;
  min-height: 260px;
  resize: vertical;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 14px;
  font: inherit;
  line-height: 1.5;
  color: var(--color-ink);
  margin-bottom: 18px;
  background: var(--color-surface-soft);
  outline: none;
}

textarea:focus,
input[type="file"]:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(11, 95, 255, 0.12);
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

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

button:disabled {
  opacity: 0.65;
  cursor: wait;
}

.result-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}

.result-header h2 {
  margin-bottom: 0;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 22px;
}

.score-grid > div {
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

.score-grid strong {
  font-size: 1.6rem;
}

.evidence-list {
  padding-left: 18px;
  color: #344054;
  line-height: 1.55;
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

.context-card p {
  margin: 0;
  color: var(--color-muted);
  line-height: 1.45;
}

.report-panel {
  margin-top: 18px;
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

.muted {
  color: var(--color-muted);
  background: #f2f4f7;
}

.high {
  color: var(--color-danger);
  background: #fff1f0;
}

.medium {
  color: var(--color-warning);
  background: #fff7ed;
}

.low {
  color: var(--color-safe);
  background: #ecfdf3;
}

@media (max-width: 860px) {
  .hero,
  .workspace,
  .trust-strip {
    grid-template-columns: 1fr;
  }

  .topbar {
    align-items: flex-start;
    flex-direction: column;
    margin-bottom: 28px;
  }

  .nav-links {
    width: 100%;
    justify-content: space-between;
  }

  h1 {
    font-size: 2.7rem;
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
          <a href="#scan">Scan</a>
          <a href="#report">Report</a>
          <a href="#system">System</a>
        </nav>
      </header>

      <section class="hero">
        <div>
          <p class="eyebrow">Privacy-first verification engine</p>
          <h1>TruthShield Lite</h1>
          <p class="lede">
            Analyze suspicious messages, fake job offers, phishing emails, screenshots, and documents before you click, pay, share, or trust.
          </p>
          <div class="hero-actions">
            <a class="primary-link" href="#scan">Start scan</a>
            <button class="ghost-button" id="sampleButton" type="button">Load sample</button>
          </div>
        </div>
        <aside class="hero-card" id="system">
          <div class="status-pill" id="healthStatus">Checking backend...</div>
          <dl class="system-metrics">
            <div>
              <dt>Storage</dt>
              <dd>Local-first</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>No database</dd>
            </div>
            <div>
              <dt>Output</dt>
              <dd>Evidence report</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section class="trust-strip" aria-label="Capabilities">
        <span>Phishing signals</span>
        <span>Fake job patterns</span>
        <span>Suspicious links</span>
        <span>Document risk</span>
      </section>

      <section class="workspace" id="scan">
        <form id="scanForm" class="panel">
          <div class="panel-heading">
            <span class="section-kicker">Input</span>
            <h2>Scan suspicious content</h2>
            <p>Paste the message exactly as received. Add a screenshot or document if you have one.</p>
          </div>

          <label for="textInput">Message, email, job offer, or notice</label>
          <textarea id="textInput" placeholder="Paste suspicious content here..."></textarea>

          <label for="fileInput">Optional screenshot or document</label>
          <div class="file-control">
            <input id="fileInput" type="file" />
            <span id="fileName">No file selected</span>
          </div>

          <div class="form-actions">
            <button type="submit" id="scanButton">Run Scan</button>
            <button type="button" class="secondary-button" id="clearButton">Clear</button>
          </div>
        </form>

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
              <span class="label">Text Risk</span>
              <strong id="textScore">--</strong>
            </div>
            <div class="score-card">
              <span class="label">File Risk</span>
              <strong id="fileScore">--</strong>
            </div>
          </div>

          <h3>Evidence</h3>
          <ul id="evidenceList" class="evidence-list">
            <li>Run a scan to see evidence.</li>
          </ul>

          <h3>Recommended Safety Context</h3>
          <div id="contextList" class="context-list"></div>
        </section>
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
const evidenceList = document.querySelector("#evidenceList");
const contextList = document.querySelector("#contextList");
const markdownReport = document.querySelector("#markdownReport");
const copyReport = document.querySelector("#copyReport");
const sampleButton = document.querySelector("#sampleButton");
const clearButton = document.querySelector("#clearButton");
const fileName = document.querySelector("#fileName");

const sampleText = `Congratulations! You are selected for a remote data analyst job with salary 90000 per month.

To confirm your joining, pay Rs 2999 processing fee today only and verify your profile at http://verify-job.xyz.

This offer is confidential and no interview is required.`;

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
  scanButton.textContent = "Scanning...";

  try {
    const file = fileInput.files[0];
    const payload = {
      text: textInput.value,
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
  } catch (error) {
    alert(error.message);
  } finally {
    scanButton.disabled = false;
    scanButton.textContent = "Run Scan";
  }
});

sampleButton.addEventListener("click", () => {
  textInput.value = sampleText;
  textInput.focus();
});

clearButton.addEventListener("click", () => {
  textInput.value = "";
  fileInput.value = "";
  fileName.textContent = "No file selected";
  riskBadge.textContent = "Waiting";
  riskBadge.className = "risk-badge muted";
  textScore.textContent = "--";
  fileScore.textContent = "--";
  evidenceList.innerHTML = "<li>Run a scan to see evidence.</li>";
  contextList.innerHTML = "";
  markdownReport.textContent = "No report yet.";
});

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "No file selected";
});

copyReport.addEventListener("click", async () => {
  await navigator.clipboard.writeText(markdownReport.textContent);
  copyReport.textContent = "Copied";
  setTimeout(() => {
    copyReport.textContent = "Copy";
  }, 1200);
});

function renderResult(result) {
  const level = result.ml_result.risk_level;
  riskBadge.textContent = `${level} Risk`;
  riskBadge.className = `risk-badge ${level.toLowerCase()}`;

  textScore.textContent = `${result.ml_result.risk_score}/100`;
  fileScore.textContent = `${result.dl_result.visual_risk_score}/100`;

  evidenceList.innerHTML = "";
  [...result.ml_result.top_reasons, ...result.dl_result.signals].forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    evidenceList.appendChild(li);
  });

  contextList.innerHTML = "";
  result.rag_context.forEach((context) => {
    const card = document.createElement("article");
    card.className = "context-card";
    card.innerHTML = `
      <h4>${escapeHtml(context.title)}</h4>
      <p>${escapeHtml(context.description)}</p>
    `;
    contextList.appendChild(card);
  });

  markdownReport.textContent = result.report_markdown;
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

checkHealth();

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

    matched = [
        token for token in ["offer", "prize", "claim", "kyc", "verify", "urgent", "payment", "invoice"]
        if token in name
    ]
    if matched:
        score += min(len(matched) * 9, 24)
        signals.append("Filename contains risk-related words: " + ", ".join(matched))
    if "image" in content_type and not any(name.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
        score += 10
        signals.append("Content type and extension do not clearly match.")

    score = max(0, min(score, 100))
    level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    return {
        "visual_risk_score": score,
        "visual_risk_level": level,
        "model_name": "TruthShield visual heuristic baseline v1",
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
    lines = [
        "# TruthShield Lite Risk Report",
        "",
        f"Scan ID: `{scan_id}`",
        "",
        "## Verdict",
        "",
        f"- Text risk: **{ml_result['risk_level']}** ({ml_result['risk_score']}/100)",
        f"- Visual/file risk: **{dl_result['visual_risk_level']}** ({dl_result['visual_risk_score']}/100)",
        "",
        "## Key Reasons",
        "",
    ]

    for reason in ml_result["top_reasons"]:
        lines.append(f"- {reason}")
    for signal in dl_result["signals"]:
        lines.append(f"- {signal}")

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


