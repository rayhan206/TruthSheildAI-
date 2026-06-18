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
  const level = result.ml_result.risk_level;
  riskBadge.textContent = `${level} Risk`;
  riskBadge.className = `risk-badge ${level.toLowerCase()}`;
  textScore.textContent = `${result.ml_result.risk_score}/100`;
  fileScore.textContent = `${result.dl_result.visual_risk_score}/100`;
  modeScore.textContent = labelMode(activeMode);

  renderCategories(result);
  renderEvidence(result);
  renderFrames(result.dl_result);
  renderContext(result.rag_context);
  renderHighlightedText(result.input_text, result.features);

  markdownReport.textContent = result.report_markdown;
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
