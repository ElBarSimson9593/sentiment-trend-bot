let distributionChart;
let timelineChart;

const brandSelect = document.getElementById("brandSelect");
const hoursSelect = document.getElementById("hoursSelect");
const refreshBtn = document.getElementById("refreshBtn");
const mentionForm = document.getElementById("mentionForm");
const brandContext = document.getElementById("brandContext");
const exampleChips = document.getElementById("exampleChips");
const crisisBtn = document.getElementById("crisisBtn");

const BRAND_INFO = {
  novahome: {
    title: "NovaHome",
    sector: "inmobiliaria ficticia",
    blurb:
      "Marca de demostración del portafolio (no es una empresa real). Al abrir el dashboard se cargan ~9 menciones repartidas en 24 h (positivas, neutras y negativas) para que el gráfico temporal y las alertas tengan sentido.",
  },
  urbacorp: {
    title: "UrbaCorp",
    sector: "marca secundaria de demo",
    blurb: "Segunda marca ficticia para mostrar filtrado por brand en el dashboard.",
  },
};

const EXAMPLES = [
  { label: "Positivo", text: "Excelente atención, muy profesionales." },
  { label: "Neutro", text: "El proceso fue normal, sin sorpresas." },
  { label: "Negativo", text: "Pésima atención, nunca más vuelvo." },
];

const trendLabels = {
  improving: "Mejorando",
  declining: "Empeorando",
  stable: "Estable",
};

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  resizeDelay: 120,
};

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function currentBrand() {
  return brandSelect.value || "novahome";
}

function currentHours() {
  return Number(hoursSelect.value || 24);
}

function setTrendClass(el, trend) {
  el.classList.remove("improving", "declining", "stable");
  el.classList.add("trend", trend);
}

function updateBrandContext(brand) {
  const info = BRAND_INFO[brand] || {
    title: brand,
    sector: "marca de demo",
    blurb: "Marca ficticia cargada en el sistema de demostración.",
  };
  brandContext.innerHTML = `
    <strong>${info.title}</strong> — ${info.sector}. ${info.blurb}
  `;
}

function renderExampleChips() {
  exampleChips.innerHTML = "";
  for (const sample of EXAMPLES) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = sample.label;
    btn.title = sample.text;
    btn.addEventListener("click", () => {
      document.getElementById("mentionText").value = sample.text;
    });
    exampleChips.appendChild(btn);
  }
}

async function postMention(text, source = "demo") {
  return fetchJson("/api/mentions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand: currentBrand(), text, source }),
  });
}

async function loadBrands() {
  const data = await fetchJson("/api/dashboard/brands");
  const previous = brandSelect.value;
  brandSelect.innerHTML = "";

  const brands = data.brands.length ? data.brands : ["novahome"];
  for (const brand of brands) {
    const option = document.createElement("option");
    option.value = brand;
    option.textContent = BRAND_INFO[brand]?.title || brand;
    brandSelect.appendChild(option);
  }

  if (previous && brands.includes(previous)) {
    brandSelect.value = previous;
  }
}

async function loadMetrics() {
  const brand = currentBrand();
  const hours = currentHours();
  updateBrandContext(brand);
  const metrics = await fetchJson(`/api/dashboard/${brand}/metrics?hours=${hours}`);

  document.getElementById("kpiTotal").textContent = metrics.total_mentions;
  document.getElementById("kpiAvg").textContent = metrics.avg_sentiment.toFixed(2);
  document.getElementById("kpiBreakdown").textContent =
    `+${metrics.positive} · ~${metrics.neutral} · -${metrics.negative}`;
  document.getElementById("kpiAlerts").textContent = metrics.recent_alerts;

  const trendEl = document.getElementById("kpiTrend");
  trendEl.textContent = trendLabels[metrics.trend] || metrics.trend;
  setTrendClass(trendEl, metrics.trend);

  const distCtx = document.getElementById("distributionChart");
  if (distributionChart) distributionChart.destroy();
  distributionChart = new Chart(distCtx, {
    type: "doughnut",
    data: {
      labels: ["Positivo", "Neutro", "Negativo"],
      datasets: [{
        data: [metrics.positive, metrics.neutral, metrics.negative],
        backgroundColor: ["#3ecf8e", "#f4c15d", "#ff6b6b"],
      }],
    },
    options: {
      ...chartDefaults,
      plugins: { legend: { labels: { color: "#e8edf7", boxWidth: 12 } } },
    },
  });

  const timeline = await fetchJson(`/api/dashboard/${brand}/timeline?hours=${hours}`);
  const timelineCtx = document.getElementById("timelineChart");
  if (timelineChart) timelineChart.destroy();
  timelineChart = new Chart(timelineCtx, {
    type: "line",
    data: {
      labels: timeline.points.map((p) => p.bucket),
      datasets: [
        {
          type: "bar",
          label: "Menciones",
          data: timeline.points.map((p) => p.count),
          backgroundColor: "rgba(154, 168, 199, 0.35)",
          borderColor: "rgba(154, 168, 199, 0.6)",
          borderWidth: 1,
          yAxisID: "yCount",
          order: 2,
        },
        {
          type: "line",
          label: "Sentimiento promedio",
          data: timeline.points.map((p) => p.avg_score),
          borderColor: "#4f8cff",
          backgroundColor: "rgba(79, 140, 255, 0.15)",
          fill: true,
          tension: 0.35,
          spanGaps: true,
          yAxisID: "yScore",
          order: 1,
          pointRadius: timeline.points.map((p) => (p.avg_score === null ? 0 : 4)),
          pointHoverRadius: 6,
        },
      ],
    },
    options: {
      ...chartDefaults,
      scales: {
        x: {
          ticks: { color: "#9aa8c7", maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
          grid: { color: "#24304a" },
        },
        yScore: {
          position: "left",
          min: -1,
          max: 1,
          ticks: { color: "#9aa8c7" },
          grid: { color: "#24304a" },
        },
        yCount: {
          position: "right",
          beginAtZero: true,
          ticks: { color: "#9aa8c7", precision: 0 },
          grid: { drawOnChartArea: false },
        },
      },
      plugins: { legend: { labels: { color: "#e8edf7" } } },
    },
  });
}

async function loadAlerts() {
  const brand = currentBrand();
  const alerts = await fetchJson(`/api/dashboard/${brand}/alerts?limit=8`);
  const list = document.getElementById("alertsList");
  list.innerHTML = "";

  if (!alerts.length) {
    list.innerHTML =
      "<li>Sin alertas aún. Usa <strong>Simular mini-crisis</strong> o envía 3 comentarios negativos en una hora.</li>";
    return;
  }

  for (const alert of alerts) {
    const item = document.createElement("li");
    item.innerHTML = `
      <time>${new Date(alert.created_at).toLocaleString("es-CL")}</time>
      <strong>${alert.negative_count} negativos</strong> · promedio ${alert.avg_score.toFixed(2)}<br />
      ${alert.message}
    `;
    list.appendChild(item);
  }
}

async function refreshDashboard() {
  await loadMetrics();
  await loadAlerts();
}

mentionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const status = document.getElementById("formStatus");
  const text = document.getElementById("mentionText").value.trim();
  const source = document.getElementById("mentionSource").value.trim() || "demo";

  try {
    const result = await postMention(text, source);
    const alertMsg = result.alert_triggered ? " · Alerta disparada" : "";
    status.textContent = `Guardado: ${result.label} (${result.sentiment_score.toFixed(2)})${alertMsg}`;
    document.getElementById("mentionText").value = "";
    await loadBrands();
    await refreshDashboard();
  } catch (error) {
    status.textContent = `Error al guardar mención: ${error.message}`;
  }
});

crisisBtn.addEventListener("click", async () => {
  const status = document.getElementById("formStatus");
  crisisBtn.disabled = true;
  status.textContent = "Simulando mini-crisis (3 negativas + alerta)…";
  try {
    const brand = currentBrand();
    const result = await fetchJson(
      `/api/demo/simulate-crisis?brand=${encodeURIComponent(brand)}`,
      { method: "POST" },
    );
    status.textContent = result.alert_triggered
      ? `Alerta creada: ${result.mentions_created} menciones negativas en la última hora.`
      : "No se pudo disparar la alerta (revisa el umbral de negativas).";
    await loadBrands();
    await refreshDashboard();
  } catch (error) {
    status.textContent = `Error en simulación: ${error.message}`;
  } finally {
    crisisBtn.disabled = false;
  }
});

brandSelect.addEventListener("change", refreshDashboard);
hoursSelect.addEventListener("change", refreshDashboard);
refreshBtn.addEventListener("click", refreshDashboard);

window.addEventListener("resize", () => {
  distributionChart?.resize();
  timelineChart?.resize();
});

(async function init() {
  renderExampleChips();
  try {
    await loadBrands();
    await refreshDashboard();
  } catch (error) {
    document.querySelector(".subtitle").textContent =
      "No se pudo cargar el dashboard. Verifica que la API esté activa.";
    console.error(error);
  }
})();
