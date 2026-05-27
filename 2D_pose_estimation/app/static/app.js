const uploadAreas = {
  front: document.getElementById("uploadAreaFront"),
  back: document.getElementById("uploadAreaBack"),
  left: document.getElementById("uploadAreaLeft"),
  right: document.getElementById("uploadAreaRight"),
};

const fileInputs = {
  front: document.getElementById("imageFront"),
  back: document.getElementById("imageBack"),
  left: document.getElementById("imageLeft"),
  right: document.getElementById("imageRight"),
};

const previews = {
  front: document.getElementById("previewFront"),
  back: document.getElementById("previewBack"),
  left: document.getElementById("previewLeft"),
  right: document.getElementById("previewRight"),
};

const previewImages = {
  front: document.getElementById("imageFrontPreview"),
  back: document.getElementById("imageBackPreview"),
  left: document.getElementById("imageLeftPreview"),
  right: document.getElementById("imageRightPreview"),
};

const statusElements = {
  front: document.getElementById("statusFront"),
  back: document.getElementById("statusBack"),
  left: document.getElementById("statusLeft"),
  right: document.getElementById("statusRight"),
};

const patientNameEl = document.getElementById("patientName");
const patientGenderEl = document.getElementById("patientGender");
const patientAgeEl = document.getElementById("patientAge");
const analyzeButton = document.getElementById("analyzeButton");
const downloadPdfBtn = document.getElementById("downloadPdfBtn");
const clearAllBtn = document.getElementById("clearAllBtn");
const statusLabel = document.getElementById("status");
const uploadedCountEl = document.getElementById("uploadedCount");
const analysisStatusEl = document.getElementById("analysisStatus");
const loadingOverlay = document.getElementById("loadingOverlay");
const removeButtons = document.querySelectorAll(".btn-remove");

const resultModal = document.getElementById("resultModal");
const closeResultModal = document.getElementById("closeResultModal");
const resultPlaceholder = document.getElementById("resultPlaceholder");
const resultContent = document.getElementById("resultContent");
const scoreGrid = document.getElementById("scoreGrid");
const patientSummary = document.getElementById("patientSummary");
const viewScores = document.getElementById("viewScores");
const recommendationBox = document.getElementById("recommendationBox");
const detailTableWrap = document.getElementById("detailTableWrap");

const TEXT = {
  empty: "未填写",
  ageSuffix: "岁",
  ready: "可分析",
  waiting: "待上传",
  invalidFile: "文件格式无效",
  fileTooLarge: "文件超过 50MB",
  invalidResult: "分析失败，未获取到有效结果",
  noRecommendation: "暂无综合建议",
  completed: "分析完成",
  completedMsg: "体态分析已完成",
  uploadAll: "请上传四个视角的照片",
  failed: "分析失败",
  detail: "详细",
  uploadFirst: "请先完成分析再生成 PDF",
  generatingPdf: "正在生成...",
  pdfGenerated: "PDF 已生成",
  pdfFailed: "PDF 生成失败",
  uploadState: "待上传",
  labels: {
    name: "姓名",
    gender: "性别",
    age: "年龄",
    reportTime: "报告时间",
    overallScore: "综合体态分",
    symmetryScore: "对称性评分",
    stabilityScore: "稳定性评分",
    indicator: "指标",
    result: "结果",
    reportTitle: "体态估计报告",
    generatedAt: "生成时间",
    uploadedStatus: "上传状态",
    viewScores: "视角评分",
    recommendation: "综合建议",
    detailData: "详细数据",
    uploadedPhotos: "上传照片",
  },
  views: {
    front: "正面",
    back: "背面",
    left: "左侧",
    right: "右侧",
  },
};

const files = {
  front: null,
  back: null,
  left: null,
  right: null,
};

let analysisResult = null;

function setStatus(text, type = "info") {
  if (!text) {
    statusLabel.textContent = "";
    statusLabel.className = "status-message";
    return;
  }

  statusLabel.textContent = text;
  statusLabel.className = `status-message show ${type}`;

  if (type === "error") {
    window.setTimeout(() => {
      if (statusLabel.textContent === text) {
        statusLabel.className = "status-message";
      }
    }, 4000);
  }
}

function showLoading(show = true) {
  loadingOverlay.style.display = show ? "flex" : "none";
}

function openResultModal() {
  if (!resultModal) {
    console.error("未找到 resultModal，请检查 index.html 中是否存在 id='resultModal'");
    return;
  }

  resultModal.style.display = "flex";
  resultModal.style.visibility = "visible";
  resultModal.style.opacity = "1";
  document.body.style.overflow = "hidden";
}

function closeModal() {
  resultModal.style.display = "none";
  document.body.style.overflow = "";
}

function getPatientInfo() {
  return {
    name: patientNameEl.value.trim() || TEXT.empty,
    gender: patientGenderEl.value || TEXT.empty,
    age: patientAgeEl.value ? `${patientAgeEl.value}${TEXT.ageSuffix}` : TEXT.empty,
  };
}

function getUploadedCount() {
  return Object.values(files).filter(Boolean).length;
}

function updateUploadCount() {
  const count = getUploadedCount();
  const ready = count === 4;

  uploadedCountEl.textContent = `${count}/4`;
  analysisStatusEl.textContent = ready ? TEXT.ready : TEXT.waiting;
  analyzeButton.disabled = !ready;
}

function resetResults() {
  analysisResult = null;

  resultPlaceholder.style.display = "grid";
  resultContent.style.display = "none";
  resultModal.style.display = "none";
  document.body.style.overflow = "";

  downloadPdfBtn.disabled = true;
  downloadPdfBtn.textContent = "生成 PDF";

  scoreGrid.innerHTML = "";
  patientSummary.innerHTML = "";
  viewScores.innerHTML = "";
  recommendationBox.textContent = "";
  detailTableWrap.innerHTML = "";
}

function clearViewFile(view) {
  files[view] = null;
  fileInputs[view].value = "";

  uploadAreas[view].style.display = "grid";
  previews[view].style.display = "none";

  statusElements[view].textContent = "";
  statusElements[view].className = "upload-status";

  updateUploadCount();
}

function handleFileSelect(view, file) {
  if (!file || !file.type.startsWith("image/")) {
    statusElements[view].textContent = TEXT.invalidFile;
    statusElements[view].className = "upload-status error";
    return;
  }

  if (file.size > 50 * 1024 * 1024) {
    statusElements[view].textContent = TEXT.fileTooLarge;
    statusElements[view].className = "upload-status error";
    return;
  }

  files[view] = file;

  const reader = new FileReader();
  reader.onload = (event) => {
    previewImages[view].src = event.target.result;
    uploadAreas[view].style.display = "none";
    previews[view].style.display = "block";
    statusElements[view].textContent = file.name;
    statusElements[view].className = "upload-status success";
  };

  reader.readAsDataURL(file);
  updateUploadCount();
}

function formatScore(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "N/A";
  }

  return value <= 1 ? (value * 100).toFixed(1) : value.toFixed(1);
}

function createSummaryItem(label, value) {
  return `
    <div class="summary-item">
      <span class="summary-item-label">${label}</span>
      <span class="summary-item-value">${value}</span>
    </div>
  `;
}

function formatDetailValue(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "number") {
    return formatScore(value);
  }

  if (Array.isArray(value)) {
    return value.length ? value.map(formatDetailValue).join("；") : "无";
  }

  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => `${key}: ${formatDetailValue(val)}`)
      .join("；");
  }

  return String(value);
}

function shouldSkipDetailKey(key) {
  return [
    "type",
    "level",
    "error",
    "posture_score",
  ].includes(key);
}

function normalizeDetailValue(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "number") {
    return formatScore(value);
  }

  if (Array.isArray(value)) {
    return value.map(normalizeDetailValue).join("，");
  }

  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => `${key}：${normalizeDetailValue(val)}`)
      .join("；");
  }

  return String(value);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function collectMetricDetailLines(metricValue) {
  const lines = [];

  function addLine(key, value) {
    if (value === null || value === undefined) {
      return;
    }

    if (typeof value === "object" && !Array.isArray(value)) {
      Object.entries(value).forEach(([childKey, childValue]) => {
        if (shouldSkipDetailKey(childKey)) {
          return;
        }
        addLine(`${key}.${childKey}`, childValue);
      });
      return;
    }

    lines.push({
      key,
      value: normalizeDetailValue(value),
    });
  }

  Object.entries(metricValue).forEach(([key, val]) => {
    if (shouldSkipDetailKey(key)) {
      return;
    }
    addLine(key, val);
  });

  return lines;
}

function formatMetricResultCell(metricValue) {
  const lines = collectMetricDetailLines(metricValue);

  if (!lines.length) {
    return "-";
  }

  return `
    <div class="detail-lines">
      ${lines
        .map(
          (line) => `
            <div class="detail-line">
              <span class="detail-line-key">${escapeHtml(line.key)}：</span>
              <span class="detail-line-value">${escapeHtml(line.value)}</span>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function getMetricRows(analysis) {
  const rows = [];

  Object.entries(TEXT.views).forEach(([viewKey, viewLabel]) => {
    const viewData = analysis[viewKey] || {};

    Object.entries(viewData).forEach(([metricName, metricValue]) => {
      if (metricName === "posture_score") {
        return;
      }

      if (!metricValue || typeof metricValue !== "object") {
        return;
      }

      if (metricValue.error) {
        rows.push({
          view: viewLabel,
          metric: metricName,
          level: metricValue.level || "未计算",
          result: escapeHtml(metricValue.error),
        });
        return;
      }

      rows.push({
        view: viewLabel,
        metric: metricName,
        level: metricValue.level || "-",
        result: formatMetricResultCell(metricValue),
      });
    });
  });

  return rows;
}

function renderScores(merged) {
  const cards = [
    {
      label: TEXT.labels.overallScore,
      value: formatScore(merged.overall_posture_score),
    },
    {
      label: TEXT.labels.symmetryScore,
      value: formatScore(merged.symmetry_score),
    },
    {
      label: TEXT.labels.stabilityScore,
      value: formatScore(merged.stability_score),
    },
  ];

  scoreGrid.innerHTML = cards
    .map(
      (card) => `
        <article class="score-card">
          <span>${card.label}</span>
          <strong>${card.value}</strong>
        </article>
      `
    )
    .join("");
}

function renderPatientSummary() {
  const info = getPatientInfo();

  patientSummary.innerHTML = [
    createSummaryItem(TEXT.labels.name, info.name),
    createSummaryItem(TEXT.labels.gender, info.gender),
    createSummaryItem(TEXT.labels.age, info.age),
    createSummaryItem(TEXT.labels.reportTime, new Date().toLocaleString("zh-CN")),
  ].join("");
}

function renderViewScores(analysis) {
  viewScores.innerHTML = Object.entries(TEXT.views)
    .map(([key, label]) => {
      const value =
        analysis[key] && typeof analysis[key].posture_score === "number"
          ? formatScore(analysis[key].posture_score)
          : "N/A";

      return createSummaryItem(label, value);
    })
    .join("");
}

function renderDetailsTable(analysis) {
  const metricRows = getMetricRows(analysis).map(
    (row) => `
      <tr>
        <td>${row.view}</td>
        <td>${row.metric}</td>
        <td>${row.level}</td>
        <td>${row.result}</td>
      </tr>
    `
  );

  detailTableWrap.innerHTML = `
    <table class="detail-table">
      <thead>
        <tr>
          <th>视角</th>
          <th>${TEXT.labels.indicator}</th>
          <th>等级</th>
          <th>${TEXT.labels.result}</th>
        </tr>
      </thead>
      <tbody>${metricRows.join("")}</tbody>
    </table>
  `;
}

function renderResult(data) {
  if (!data || !data.success) {
    setStatus(TEXT.invalidResult, "error");
    return;
  }

  const analysis = data.analysis_result || {};
  const merged = analysis.merged || {};

  analysisResult = data;

  renderScores(merged);
  renderPatientSummary();
  renderViewScores(analysis);

  recommendationBox.textContent = merged.recommendation || TEXT.noRecommendation;

  renderDetailsTable(analysis);

  resultPlaceholder.style.display = "none";
  resultContent.style.display = "grid";
  downloadPdfBtn.disabled = false;

  analysisStatusEl.textContent = TEXT.completed;
  setStatus(TEXT.completedMsg, "success");

  // 关键：分析完成后打开弹窗
  openResultModal();
}

async function analyzeImage() {
  if (Object.values(files).some((file) => file === null)) {
    setStatus(TEXT.uploadAll, "error");
    return;
  }

  showLoading(true);
  analyzeButton.disabled = true;
  downloadPdfBtn.disabled = true;

  const formData = new FormData();
  formData.append("file_front", files.front);
  formData.append("file_back", files.back);
  formData.append("file_left", files.left);
  formData.append("file_right", files.right);

  try {
    const response = await fetch("/posture/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "未知错误",
      }));

      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    renderResult(result);
  } catch (error) {
    setStatus(`${TEXT.failed}：${error.message}`, "error");
    analysisStatusEl.textContent = TEXT.failed;
  } finally {
    showLoading(false);
    analyzeButton.disabled = getUploadedCount() !== 4;
  }
}

function buildPdfHtml() {
  const info = getPatientInfo();
  const analysis = analysisResult ? analysisResult.analysis_result || {} : {};
  const merged = analysis.merged || {};

  const viewItems = [
    [TEXT.views.front, analysis.front?.posture_score],
    [TEXT.views.back, analysis.back?.posture_score],
    [TEXT.views.left, analysis.left?.posture_score],
    [TEXT.views.right, analysis.right?.posture_score],
  ];

  const detailRows = getMetricRows(analysis)
    .map(
      (row) => `
        <tr>
          <td>${row.view}</td>
          <td>${row.metric}</td>
          <td>${row.level}</td>
          <td>${row.result}</td>
        </tr>
      `
    )
    .join("");

  return `
    <div class="pdf-report">
      <div class="pdf-header">
        <h1>${TEXT.labels.reportTitle}</h1>
        <p>${TEXT.labels.generatedAt}: ${new Date().toLocaleString("zh-CN")}</p>
      </div>

      <div class="pdf-meta">
        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.name}</span>
          <span class="pdf-value">${info.name}</span>
        </div>

        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.gender}</span>
          <span class="pdf-value">${info.gender}</span>
        </div>

        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.age}</span>
          <span class="pdf-value">${info.age}</span>
        </div>

        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.uploadedStatus}</span>
          <span class="pdf-value">${uploadedCountEl.textContent}</span>
        </div>
      </div>

      <div class="pdf-score-grid">
        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.overallScore}</span>
          <span class="pdf-value">${formatScore(merged.overall_posture_score)}</span>
        </div>

        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.symmetryScore}</span>
          <span class="pdf-value">${formatScore(merged.symmetry_score)}</span>
        </div>

        <div class="pdf-card">
          <span class="pdf-label">${TEXT.labels.stabilityScore}</span>
          <span class="pdf-value">${formatScore(merged.stability_score)}</span>
        </div>
      </div>

      <div class="pdf-section">
        <h3>${TEXT.labels.viewScores}</h3>
        <div class="pdf-view-grid">
          ${viewItems
            .map(
              ([label, value]) => `
                <div class="pdf-card">
                  <span class="pdf-label">${label}</span>
                  <span class="pdf-value">${formatScore(value)}</span>
                </div>
              `
            )
            .join("")}
        </div>
      </div>

      <div class="pdf-section">
        <h3>${TEXT.labels.recommendation}</h3>
        <div class="pdf-recommendation">
          ${merged.recommendation || TEXT.noRecommendation}
        </div>
      </div>

      <div class="pdf-section">
        <h3>${TEXT.labels.detailData}</h3>
        <table>
          <thead>
            <tr>
              <th>视角</th>
              <th>${TEXT.labels.indicator}</th>
              <th>等级</th>
              <th>${TEXT.labels.result}</th>
            </tr>
          </thead>
          <tbody>${detailRows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function getSafeFileName(name) {
  return String(name || TEXT.empty)
    .trim()
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "_") || TEXT.empty;
}

async function exportPdf() {
  if (!analysisResult) {
    setStatus(TEXT.uploadFirst, "error");
    return;
  }

  if (typeof html2pdf === "undefined") {
    setStatus("PDF 生成库加载失败，请检查网络或 html2pdf.js 引入路径", "error");
    return;
  }

  const info = getPatientInfo();
  const safeName = getSafeFileName(info.name);
  const fileName = `体态估计结果_${safeName}.pdf`;

  const tempContainer = document.createElement("div");
  tempContainer.style.position = "fixed";
  tempContainer.style.left = "-9999px";
  tempContainer.style.top = "0";
  tempContainer.style.width = "794px";
  tempContainer.innerHTML = buildPdfHtml();

  document.body.appendChild(tempContainer);

  const reportEl = tempContainer.querySelector(".pdf-report");

  const options = {
    margin: 0,
    filename: fileName,
    image: {
      type: "jpeg",
      quality: 0.98,
    },
    html2canvas: {
      scale: 2,
      useCORS: true,
      backgroundColor: "#ffffff",
      scrollY: 0,
    },
    jsPDF: {
      unit: "px",
      format: [794, 1123],
      orientation: "portrait",
    },
    pagebreak: {
      mode: ["css", "legacy"],
      avoid: [".pdf-card", ".pdf-photo-card", ".pdf-section"],
    },
  };

  try {
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.textContent = TEXT.generatingPdf;

    await html2pdf().set(options).from(reportEl).save();

    setStatus(`${TEXT.pdfGenerated}：${fileName}`, "success");
  } catch (error) {
    setStatus(`${TEXT.pdfFailed}：${error.message}`, "error");
  } finally {
    document.body.removeChild(tempContainer);
    downloadPdfBtn.disabled = false;
    downloadPdfBtn.textContent = "生成 PDF";
  }
}

Object.entries(uploadAreas).forEach(([view, area]) => {
  area.addEventListener("click", () => {
    fileInputs[view].click();
  });

  area.addEventListener("dragover", (event) => {
    event.preventDefault();
    area.classList.add("drag-over");
  });

  area.addEventListener("dragleave", () => {
    area.classList.remove("drag-over");
  });

  area.addEventListener("drop", (event) => {
    event.preventDefault();
    area.classList.remove("drag-over");

    const file = event.dataTransfer.files[0];

    if (file) {
      handleFileSelect(view, file);
    }
  });

  fileInputs[view].addEventListener("change", (event) => {
    const file = event.target.files[0];

    if (file) {
      handleFileSelect(view, file);
    }
  });
});

removeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    clearViewFile(button.dataset.view);
    resetResults();
  });
});

clearAllBtn.addEventListener("click", () => {
  Object.keys(files).forEach((view) => clearViewFile(view));

  patientNameEl.value = "";
  patientGenderEl.value = "";
  patientAgeEl.value = "";

  analysisStatusEl.textContent = TEXT.uploadState;

  setStatus("", "info");
  resetResults();
});

analyzeButton.addEventListener("click", analyzeImage);
downloadPdfBtn.addEventListener("click", exportPdf);

closeResultModal.addEventListener("click", closeModal);

resultModal.addEventListener("click", (event) => {
  if (event.target === resultModal) {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && resultModal.style.display === "flex") {
    closeModal();
  }
});

updateUploadCount();
resetResults();