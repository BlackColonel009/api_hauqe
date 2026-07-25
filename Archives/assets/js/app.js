(function () {
  "use strict";

  const data = window.HAUQE_MOCK;
  const $ = (selector) => document.querySelector(selector);

  function icon(name) {
    return `<i data-lucide="${name}"></i>`;
  }

  function renderMetrics() {
    $("#metricsGrid").innerHTML = data.metrics.map((item) => `
      <article class="metric-card">
        <div class="metric-icon ${item.tone}">${icon(item.icon)}</div>
        <div class="metric-copy">
          <span>${item.label}</span>
          <div class="metric-value"><strong>${item.value}</strong><b class="${item.trend}">${item.delta}</b></div>
          <small>${item.note}</small>
        </div>
      </article>
    `).join("");
  }

  function renderLegend() {
    const total = data.statuses.reduce((sum, item) => sum + item.value, 0);
    $("#statusLegend").innerHTML = data.statuses.map((item) => `
      <div><span><i style="background:${item.color}"></i>${item.label}</span><strong>${item.value}</strong><small>${Math.round(item.value / total * 100)} %</small></div>
    `).join("");
  }

  function renderPriorities() {
    $("#priorityList").innerHTML = data.priorities.map((item) => `
      <button class="priority-item" type="button">
        <span class="priority-icon ${item.level}">${icon(item.icon)}</span>
        <span><strong>${item.title}</strong><small>${item.meta}</small></span>
        ${icon("chevron-right")}
      </button>
    `).join("");
  }

  function renderRecent() {
    $("#recentTable").innerHTML = data.recent.map((row) => `
      <tr>
        <td><div class="company-cell"><span>${row.initials}</span><div><strong>${row.company}</strong><small>${row.sector}</small></div></div></td>
        <td><strong>${row.certification}</strong><small class="d-block text-muted">${row.code}</small></td>
        <td>${row.body}</td>
        <td><strong>${row.expiry}</strong><small class="d-block ${row.days.includes("18") ? "text-danger" : "text-muted"}">${row.days}</small></td>
        <td><span class="status-badge ${row.statusTone}"><i></i>${row.status}</span></td>
        <td><div class="score-cell"><strong>${row.score}</strong><span><i style="width:${row.score}%"></i></span></div></td>
        <td><button class="more-button" aria-label="Actions pour ${row.company}">${icon("ellipsis-vertical")}</button></td>
      </tr>
    `).join("");
  }

  function createCharts() {
    if (typeof Chart === "undefined") return;
    Chart.defaults.font.family = "DM Sans, sans-serif";
    Chart.defaults.color = "#667085";

    new Chart($("#statusChart"), {
      type: "doughnut",
      data: {
        labels: data.statuses.map((item) => item.label),
        datasets: [{ data: data.statuses.map((item) => item.value), backgroundColor: data.statuses.map((item) => item.color), borderWidth: 0, hoverOffset: 3 }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: "72%", plugins: { legend: { display: false }, tooltip: { padding: 12, displayColors: true } } },
      plugins: [{ id: "centerText", afterDraw(chart) { const { ctx, chartArea } = chart; const x = (chartArea.left + chartArea.right) / 2; const y = (chartArea.top + chartArea.bottom) / 2; ctx.save(); ctx.textAlign = "center"; ctx.fillStyle = "#13251f"; ctx.font = "800 28px Manrope"; ctx.fillText("212", x, y - 2); ctx.fillStyle = "#7b8883"; ctx.font = "500 12px DM Sans"; ctx.fillText("certifications", x, y + 18); ctx.restore(); } }]
    });

    new Chart($("#activityChart"), {
      type: "line",
      data: {
        labels: data.activity.labels,
        datasets: [
          { label: "Actives", data: data.activity.active, borderColor: "#178a60", backgroundColor: "rgba(23,138,96,.09)", fill: true, tension: .38, borderWidth: 2.5, pointRadius: 3 },
          { label: "Renouvelées", data: data.activity.renewed, borderColor: "#3c72d9", tension: .38, borderWidth: 2, pointRadius: 3 },
          { label: "Expirées", data: data.activity.expired, borderColor: "#dc5a55", tension: .38, borderWidth: 2, pointRadius: 3 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, interaction: { intersect: false, mode: "index" }, scales: { x: { grid: { display: false } }, y: { beginAtZero: true, grid: { color: "#edf1ef" }, border: { display: false } } }, plugins: { legend: { position: "bottom", align: "start", labels: { usePointStyle: true, boxWidth: 7, padding: 18 } } } }
    });
  }

  function bindNavigation() {
    $("#menuToggle").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
    document.querySelectorAll(".sidebar .nav-link").forEach((link) => link.addEventListener("click", (event) => {
      event.preventDefault();
      document.querySelectorAll(".sidebar .nav-link").forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    }));
  }

  renderMetrics();
  renderLegend();
  renderPriorities();
  renderRecent();
  bindNavigation();
  if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  createCharts();
})();
