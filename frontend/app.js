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
