(function () {
  "use strict";

  const data = window.HAUQE_MOCK;
  const $ = (selector) => document.querySelector(selector);

  function icon(name) {
    return `<i data-lucide="${name}"></i>`;
  }

  function renderMetrics() {
    $("#metricsGrid").innerHTML = data.metrics.map((item,index) => `
      <article class="metric-card dashboard-clickable" data-metric="${index}" tabindex="0" role="button">
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
    $("#priorityList").innerHTML = data.priorities.map((item,index) => `
      <button class="priority-item" type="button" data-priority="${index}">
        <span class="priority-icon ${item.level}">${icon(item.icon)}</span>
        <span><strong>${item.title}</strong><small>${item.meta}</small></span>
        ${icon("chevron-right")}
      </button>
    `).join("");
  }

  function renderRecent() {
    $("#recentTable").innerHTML = data.recent.map((row,index) => `
      <tr class="dashboard-clickable" data-recent="${index}" tabindex="0">
        <td><div class="company-cell"><span>${row.initials}</span><div><strong>${row.company}</strong><small>${row.sector}</small></div></div></td>
        <td><strong>${row.certification}</strong><small class="d-block text-muted">${row.code}</small></td>
        <td>${row.body}</td>
        <td><strong>${row.expiry}</strong><small class="d-block ${row.days.includes("18") ? "text-danger" : "text-muted"}">${row.days}</small></td>
        <td><span class="status-badge ${row.statusTone}"><i></i>${row.status}</span></td>
        <td><div class="score-cell"><strong>${row.score}</strong><span><i style="width:${row.score}%"></i></span></div></td>
        <td><button class="more-button" data-recent-menu="${index}" aria-label="Actions pour ${row.company}">${icon("ellipsis-vertical")}</button></td>
      </tr>
    `).join("");
  }

  function createCharts() {
    if (typeof Chart === "undefined") return;
    Chart.defaults.font.family = "DM Sans, sans-serif";
    Chart.defaults.color = "#667085";

    const statusChart = new Chart($("#statusChart"), {
      type: "doughnut",
      data: {
        labels: data.statuses.map((item) => item.label),
        datasets: [{ data: data.statuses.map((item) => item.value), backgroundColor: data.statuses.map((item) => item.color), borderWidth: 0, hoverOffset: 3 }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: "72%", plugins: { legend: { display: false }, tooltip: { padding: 12, displayColors: true } } },
      plugins: [{ id: "centerText", afterDraw(chart) { const { ctx, chartArea } = chart; const x = (chartArea.left + chartArea.right) / 2; const y = (chartArea.top + chartArea.bottom) / 2; const dark=document.documentElement.dataset.theme==="dark";ctx.save(); ctx.textAlign = "center"; ctx.fillStyle = dark?"#edf7f3":"#13251f"; ctx.font = "800 28px Manrope"; ctx.fillText("212", x, y - 2); ctx.fillStyle = dark?"#a9beb7":"#7b8883"; ctx.font = "500 12px DM Sans"; ctx.fillText("certifications", x, y + 18); ctx.restore(); } }]
    });

    const activityChart = new Chart($("#activityChart"), {
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
    window.addEventListener("hauqe:theme-change",()=>{const dark=document.documentElement.dataset.theme==="dark";Chart.defaults.color=dark?"#a9beb7":"#667085";activityChart.options.scales.y.grid.color=dark?"#294a41":"#edf1ef";statusChart.draw();activityChart.update()},{once:false});
  }

  function bindNavigation() {
    $("#menuToggle").addEventListener("click", () => $("#sidebar").classList.toggle("open"));
    document.querySelectorAll(".sidebar .nav-link").forEach((link) => link.addEventListener("click", (event) => {
      event.preventDefault();
      document.querySelectorAll(".sidebar .nav-link").forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    }));
  }

  function go(route){ location.hash=`#/${route}`; }
  function toast(message){let box=document.querySelector("#dashboardToast");if(!box){box=document.createElement("div");box.id="dashboardToast";box.className="dashboard-toast";box.innerHTML=`${icon("circle-check")}<span></span>`;document.body.appendChild(box)}box.querySelector("span").textContent=message;box.classList.add("show");if(window.lucide)window.lucide.createIcons({attrs:{"stroke-width":1.8}});clearTimeout(box.timer);box.timer=setTimeout(()=>box.classList.remove("show"),1800)}
  function closeMenu(){document.querySelector("#dashboardActionMenu")?.remove()}
  function menu(anchor,items){closeMenu();const box=document.createElement("div");box.id="dashboardActionMenu";box.className="dashboard-action-menu";box.innerHTML=items.map((x,i)=>`<button data-menu-action="${i}"><i data-lucide="${x[0]}"></i><span><strong>${x[1]}</strong><small>${x[2]}</small></span></button>`).join("");document.body.appendChild(box);const r=anchor.getBoundingClientRect();box.style.top=`${Math.min(r.bottom+7,innerHeight-box.offsetHeight-12)}px`;box.style.left=`${Math.max(12,Math.min(r.right-box.offsetWidth,innerWidth-box.offsetWidth-12))}px`;box.querySelectorAll("button").forEach((b,i)=>b.onclick=()=>{closeMenu();items[i][3]()});if(window.lucide)window.lucide.createIcons({attrs:{"stroke-width":1.8}})}
  function bindDashboardActions(){
    const headingButtons=document.querySelectorAll(".page-heading .heading-actions button");if(headingButtons[0])headingButtons[0].onclick=()=>toast("Export du tableau de bord préparé");if(headingButtons[1])headingButtons[1].onclick=()=>go("collectes/nouveau");
    document.querySelector(".filter-bar .reset-filter").onclick=()=>{document.querySelectorAll(".filter-bar select").forEach(x=>x.selectedIndex=0);toast("Filtres réinitialisés")};document.querySelectorAll(".filter-bar select").forEach(x=>x.onchange=()=>toast(`Filtre appliqué : ${x.selectedOptions[0].text}`));
    const metricRoutes=["entreprises","certifications","entreprises","echeances"];document.querySelectorAll("[data-metric]").forEach(card=>{const open=()=>go(metricRoutes[+card.dataset.metric]);card.onclick=open;card.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();open()}}});
    document.querySelectorAll("[data-priority]").forEach((button)=>button.onclick=()=>{const routes=["echeances","validations","echeances"];go(routes[+button.dataset.priority])});
    const deadlineLink=[...document.querySelectorAll(".deadline-panel a")][0];if(deadlineLink)deadlineLink.onclick=e=>{e.preventDefault();go("echeances")};const nextDeadline=document.querySelector(".next-deadline");if(nextDeadline){nextDeadline.classList.add("dashboard-clickable");nextDeadline.onclick=()=>go("echeances")};
    const alertLink=document.querySelector(".priority-panel .panel-footer-link");if(alertLink)alertLink.onclick=e=>{e.preventDefault();go("alertes")};const registerLink=document.querySelector(".table-panel .panel-heading a");if(registerLink)registerLink.onclick=e=>{e.preventDefault();go("certifications")};
    document.querySelectorAll("[data-recent]").forEach(row=>{const open=()=>go(`certifications/${+row.dataset.recent+1}`);row.onclick=e=>{if(!e.target.closest("button"))open()};row.onkeydown=e=>{if(e.key==="Enter")open()}});
    document.querySelectorAll("[data-recent-menu]").forEach(button=>button.onclick=e=>{e.stopPropagation();const row=data.recent[+button.dataset.recentMenu];menu(button,[["eye","Ouvrir le certificat",row.certification,()=>go(`certifications/${+button.dataset.recentMenu+1}`)],["building-2","Voir l’entreprise",row.company,()=>go(`entreprises/${+button.dataset.recentMenu+1}`)],["calendar-clock","Consulter l’échéance",row.expiry,()=>go("echeances")]])});
    const chartMenu=document.querySelector(".chart-panel .more-button");if(chartMenu)chartMenu.onclick=()=>menu(chartMenu,[["list","Voir le registre","Toutes les certifications",()=>go("certifications")],["download","Exporter le graphique","Image ou rapport",()=>toast("Graphique préparé pour l’export")]]);
    document.querySelector(".activity-panel .compact-select").onchange=e=>toast(`Période du graphique : ${e.target.value}`);
    document.addEventListener("click",e=>{if(!e.target.closest("#dashboardActionMenu,.more-button"))closeMenu()},{once:false});
  }

  renderMetrics();
  renderLegend();
  renderPriorities();
  renderRecent();
  if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  createCharts();
  bindDashboardActions();
})();
