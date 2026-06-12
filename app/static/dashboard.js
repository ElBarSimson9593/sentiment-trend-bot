let distributionChart;
let timelineChart;

const brandSelect = document.getElementById("brandSelect");
const hoursSelect = document.getElementById("hoursSelect");
const refreshBtn = document.getElementById("refreshBtn");
const mentionForm = document.getElementById("mentionForm");

const trendLabels = {
  improving: "Mejorando",
  declining: "Empeorando",
  stable: "Estable",
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

async function loadBrands() {
  const data = await fetchJson("/api/dashboard/brands");
  brandSelect.innerHTML = "";

  const brands = data.brands.length ? data.brands : ["novahome"];
  for (const brand of brands) {
    const option = document.createElement("option");
    option.value = brand;
    option.textContent = brand;
    brandSelect.appendChild(option);
  }
}

async function loadMetrics() {
  const brand = currentBrand();
  const hours = currentHours();
  const metrics = await fetchJson(`/api/dashboard/${brand}/metrics?hours=${hours}`);

  document.getElementById("kpiTotal").textContent = metrics.total_mentions;
  document.getElementById("kpiAvg").textContent = metrics.avg_sentiment.toFixed(2);
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
      plugins: { legend: { labels: { color: "#e8edf7" } } },
    },
  });

  const timeline = await fetchJson(`/api/dashboard/${brand}/timeline?hours=${hours}`);
  const timelineCtx = document.getElementById("timelineChart");
  if (timelineChart) timelineChart.destroy();
  timelineChart = new Chart(timelineCtx, {
    type: "line",
    data: {
      labels: timeline.points.map((p) => p.bucket),
      datasets: [{
        label: "Sentimiento promedio",
        data: timeline.points.map((p) => p.avg_score),
        borderColor: "#4f8cff",
        backgroundColor: "rgba(79, 140, 255, 0.15)",
        fill: true,
        tension: 0.35,
        spanGaps: true,
        pointRadius: timeline.points.map((p) => (p.avg_score === null ? 0 : 4)),
        pointHoverRadius: 6,
      }],
    },
    options: {
      scales: {
        x: {
          ticks: { color: "#9aa8c7", maxRotation: 45, minRotation: 0 },
          grid: { color: "#24304a" },
        },
        y: {
          min: -1,
          max: 1,
          ticks: { color: "#9aa8c7" },
          grid: { color: "#24304a" },
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
    list.innerHTML = "<li>Sin alertas registradas para esta marca.</li>";
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
    const result = await fetchJson("/api/mentions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brand: currentBrand(), text, source }),
    });

    const alertMsg = result.alert_triggered
      ? " · ⚠️ Alerta disparada"
      : "";
    status.textContent = `Guardado: ${result.label} (${result.sentiment_score.toFixed(2)})${alertMsg}`;
    document.getElementById("mentionText").value = "";
    await loadBrands();
    await refreshDashboard();
  } catch (error) {
    status.textContent = `Error al guardar mención: ${error.message}`;
  }
});

brandSelect.addEventListener("change", refreshDashboard);
hoursSelect.addEventListener("change", refreshDashboard);
refreshBtn.addEventListener("click", refreshDashboard);

(async function init() {
  try {
    await loadBrands();
    await refreshDashboard();
  } catch (error) {
    document.querySelector(".subtitle").textContent =
      "No se pudo cargar el dashboard. ¿Está corriendo la API?";
    console.error(error);
  }
})();
