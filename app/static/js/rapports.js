(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const frDate = (value) => /^\d{4}-\d{2}-\d{2}$/.test(String(value || "")) ? `${value.slice(8, 10)}/${value.slice(5, 7)}/${value.slice(0, 4)}` : String(value || "—");
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  const reports = [
    { id: "companies", category: "Registre", title: "Situation des entreprises", desc: "Entreprises enregistrées, statuts et répartition.", icon: "building-2", url: "/api/v1/entreprises" },
    { id: "certs", category: "Registre", title: "État des certifications", desc: "Certificats, validité, référentiels et organismes.", icon: "badge-check", url: "/api/v1/certifications" },
    { id: "bodies", category: "Registre", title: "Organismes certificateurs", desc: "Reconnaissance, accréditations et couverture.", icon: "landmark", url: "/api/v1/organismes" },
    { id: "controls", category: "Contrôle", title: "Bilan des contrôles FUCCS", desc: "Contrôles, décisions et résultats des grilles.", icon: "clipboard-check", url: "/api/v1/fuccs/controles" },
    { id: "quality", category: "Qualité", title: "Revues de qualité", desc: "Revues, résultats et plans d’actions.", icon: "badge-check", url: "/api/v1/quality/reviews" },
    { id: "deadlines", category: "Pilotage", title: "Suivi des échéances", desc: "Retards, renouvellements et actions attendues.", icon: "calendar-clock", url: "/api/v1/echeances" },
    { id: "alerts", category: "Pilotage", title: "État des alertes", desc: "Alertes ouvertes, criticité et traitement.", icon: "bell-ring", url: "/api/v1/alertes" },
    { id: "audit", category: "Administration", title: "Synthèse du journal d’audit", desc: "Opérations, résultats et catégories.", icon: "scroll-text", url: "/api/v1/audit/events" },
  ];
  const institution = "HAUQE — Haute Autorité de la Qualité et de l’Environnement";
  let selected = reports[0], category = "Tous", history = [], currentRows = [], me = null;
  let bnecType = "MENSUEL";
  let previewRequestId = 0, previewPendingKey = null;
  const exportMeta = {
    companies: { date: "created_at", dateLabel: "Date d’enregistrement", region: "zone_siege_id", status: "statut" },
    certs: { date: "created_at", dateLabel: "Date d’enregistrement", status: "statut", standard: "norme_id" },
    bodies: { date: "created_at", dateLabel: "Date d’enregistrement", status: "statut" },
    controls: { date: "created_at", dateLabel: "Date du contrôle", status: "statut" },
    quality: { date: "created_at", dateLabel: "Date de la revue", status: "statut" },
    deadlines: { date: "date_echeance", dateLabel: "Date d’échéance", status: "statut" },
    alerts: { date: "date_detection", dateLabel: "Date de détection", status: "statut" },
    audit: { date: "date_evenement", dateLabel: "Date de l’évènement", status: "resultat" },
  };
  const sectionTitles = {
    identifiers: "Identifiants et références", statuses: "Statuts et résultats",
    dates: "Dates et échéances", details: "Données détaillées",
  };
  const savedConfigurations = new Map();
  let filterLoadId = 0;
  function toast(message, error = false) { const b = $("#reportToast"); b.querySelector("span").textContent = message; b.classList.toggle("error", error); b.hidden = false; setTimeout(() => b.hidden = true, 2800); }
  const normalize = (payload) => Array.isArray(payload) ? payload : (payload?.items || payload?.results || payload?.data || []);
  async function loadAllRows(baseUrl) {
    const collected = []; let offset = 0;
    for (let page = 0; page < 100; page += 1) {
      const join = baseUrl.includes("?") ? "&" : "?";
      const payload = await api.apiRequest(`${baseUrl}${join}limit=100&offset=${offset}`);
      const rows = normalize(payload); collected.push(...rows);
      const total = Number(payload?.total ?? rows.length);
      if (!rows.length || collected.length >= total || rows.length < 100) return collected;
      if (page === 99) throw new Error("Export trop volumineux pour le catalogue instantané : utilisez un périmètre plus ciblé ou un bilan BNEC.");
      offset += rows.length;
    }
    return collected;
  }
  const scalar = (v) => v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v);
  function fieldGroup(key) {
    if (/(^id$|_id$)/i.test(key)) return null;
    if (/(date|echeance|expiration|created_at|updated_at)/i.test(key)) return "dates";
    if (/(statut|etat|resultat|score|taux|niveau|classe|decision|authenticite|priorite)/i.test(key)) return "statuses";
    if (/(identifiant|numero|reference|^code$|_code$)/i.test(key)) return "identifiers";
    return "details";
  }
  function selectedSections() {
    return new Set([...document.querySelectorAll('#reportOptions input[data-section]:checked')].map((input) => input.dataset.section));
  }
  function flatten(row) {
    const out = {};
    const sections = selectedSections();
    Object.entries(row || {}).forEach(([k, v]) => {
      if (Array.isArray(v) || !sections.has(fieldGroup(k))) return;
      out[k.replaceAll("_", " ")] = scalar(v);
    });
    return out;
  }
  function displayKey(key) { return key.replace(/^\p{L}/u, (c) => c.toUpperCase()); }
  function periodDates() {
    const now = new Date(), mode = $("#reportPeriod").value;
    const end = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    if (mode === "month") return { start: `${end.slice(0, 8)}01`, end };
    if (mode === "quarter") return { start: `${now.getFullYear()}-${String(Math.floor(now.getMonth() / 3) * 3 + 1).padStart(2, "0")}-01`, end };
    if (mode === "year") return { start: `${now.getFullYear()}-01-01`, end };
    const start = $("#reportStart").value, customEnd = $("#reportEnd").value;
    if (!start || !customEnd || start > customEnd) throw new Error("Choisissez une période personnalisée valide.");
    return { start, end: customEnd };
  }
  function selectedExportFilters() {
    const period = periodDates();
    return {
      period_mode: $("#reportPeriod").value, ...period,
      region: $("#reportRegion").disabled ? null : $("#reportRegion").value || null,
      status: $("#reportStatus").disabled ? null : $("#reportStatus").value || null,
      standard: $("#reportStandard").disabled ? null : $("#reportStandard").value || null,
    };
  }
  function filterExportRows(rows, report, filters) {
    const meta = exportMeta[report.id];
    return rows.filter((row) => {
      const day = String(row[meta.date] || "").slice(0, 10);
      if (!day || day < filters.start || day > filters.end) return false;
      if (filters.region && String(row[meta.region] || "") !== filters.region) return false;
      if (filters.status && String(row[meta.status] || "") !== filters.status) return false;
      if (filters.standard && String(row[meta.standard] || "") !== filters.standard) return false;
      return true;
    });
  }
  async function loadFilteredExport() {
    if (!selectedSections().size) throw new Error("Sélectionnez au moins une rubrique de contenu.");
    const report = selected, filters = selectedExportFilters();
    const rows = await loadAllRows(report.url);
    return { rows: filterExportRows(rows, report, filters), filters };
  }
  function renderCategories() {
    const cats = ["Tous", ...new Set(reports.map((r) => r.category))];
    $("#reportCategories").innerHTML = cats.map((x) => `<button class="${x === category ? "active" : ""}" data-category="${x}">${x}</button>`).join("");
    document.querySelectorAll("[data-category]").forEach((b) => b.onclick = () => { category = b.dataset.category; renderCategories(); renderList(); }); icons();
  }
  function renderList() {
    const q = $("#reportSearch").value.toLowerCase();
    const list = reports.filter((r) => (category === "Tous" || r.category === category) && `${r.title} ${r.desc}`.toLowerCase().includes(q));
    $("#reportList").innerHTML = list.map((r) => `<button class="report-item ${r.id === selected.id ? "active" : ""}" data-report="${r.id}"><span><i data-lucide="${r.icon}"></i></span><div><strong>${r.title}</strong><small>${r.desc}</small></div><b>3 formats</b></button>`).join("");
    document.querySelectorAll("[data-report]").forEach((b) => b.onclick = () => { selected = reports.find((r) => r.id === b.dataset.report); renderList(); renderBuilder(); }); icons();
  }
  function renderBuilder() {
    $("#reportIcon").innerHTML = `<i data-lucide="${selected.icon}"></i>`; $("#reportCategory").textContent = selected.category;
    $("#reportTitle").textContent = selected.title; $("#reportDescription").textContent = selected.desc;
    const saved = savedConfigurations.get(selected.id);
    const sections = saved?.sections?.selected || Object.keys(sectionTitles);
    $("#reportOptions").innerHTML = Object.entries(sectionTitles).map(([key, title]) => `<label class="report-option"><input type="checkbox" data-section="${key}" ${sections.includes(key) ? "checked" : ""}>${title}</label>`).join("");
    $("#reportPeriod").value = saved?.filtres?.period_mode || "month";
    $("#reportStart").value = saved?.filtres?.start || "";
    $("#reportEnd").value = saved?.filtres?.end || "";
    $("#customDates").hidden = $("#reportPeriod").value !== "custom";
    const format = saved?.format?.toLowerCase() || "pdf";
    const radio = document.querySelector(`[name="reportFormat"][value="${format}"]`);
    if (radio) radio.checked = true;
    document.querySelectorAll(".format-options>label").forEach((label) => label.classList.toggle("selected", label.querySelector("input").checked));
    $("#reportRegion").closest("label").firstChild.textContent = "Zone administrative";
    $("#reportStatus").closest("label").firstChild.textContent = selected.id === "audit" ? "Résultat" : "Statut";
    populateReportFilters(selected, saved);
    icons();
  }
  function setSelectOptions(selector, items, allLabel, value) {
    const element = $(selector);
    element.innerHTML = `<option value="">${esc(allLabel)}</option>${items.map(([id, title]) => `<option value="${esc(id)}">${esc(title)}</option>`).join("")}`;
    element.disabled = items.length === 0;
    element.value = value || "";
  }
  async function populateReportFilters(report, saved) {
    const loadId = ++filterLoadId, meta = exportMeta[report.id];
    setSelectOptions("#reportRegion", [], "Sans objet pour ce rapport", null);
    setSelectOptions("#reportStatus", [], "Chargement des statuts…", null);
    setSelectOptions("#reportStandard", [], "Sans objet pour ce rapport", null);
    try {
      const rows = await loadAllRows(report.url);
      if (loadId !== filterLoadId || selected.id !== report.id) return;
      const statuses = [...new Set(rows.map((row) => row[meta.status]).filter(Boolean).map(String))].sort((a, b) => a.localeCompare(b, "fr"));
      setSelectOptions("#reportStatus", statuses.map((value) => [value, value.replaceAll("_", " ")]), "Tous les statuts", saved?.filtres?.status);
      if (report.id === "companies") {
        const options = await api.apiGet("/api/v1/entreprises/filters");
        if (loadId !== filterLoadId || selected.id !== report.id) return;
        setSelectOptions("#reportRegion", (options.zones || []).map((zone) => [zone.id, zone.nom]), "Toutes les zones", saved?.filtres?.region);
      }
      if (report.id === "certs") {
        const options = await api.apiGet("/api/v1/certifications/filters");
        if (loadId !== filterLoadId || selected.id !== report.id) return;
        setSelectOptions("#reportStandard", (options.norms || []).map((norm) => [norm.id, norm.code || norm.label]), "Tous les référentiels", saved?.filtres?.standard);
      }
    } catch (error) {
      if (loadId === filterLoadId && selected.id === report.id) toast(`Filtres indisponibles : ${error.message}`, true);
    }
  }
  function statusFr(v) {
    const s = String(v || "DEMANDE").toUpperCase();
    return ({ DEMANDE: "Demandé", EN_GENERATION: "En génération", GENERE: "Généré", ECHEC: "Échec" })[s] || s.replaceAll("_", " ");
  }
  function renderHistory() {
    const q = $("#historySearch").value.toLowerCase();
    const rows = history.filter((x) => `${x.nom_modele} ${x.categorie} ${x.format}`.toLowerCase().includes(q));
    $("#reportHistoryRows").innerHTML = rows.length ? rows.map((x) => `<tr><td><div class="history-report"><span class="${String(x.format).toLowerCase()}"><i data-lucide="file-text"></i></span><div><strong>${esc(x.nom_modele)}</strong><small>${esc(x.code_modele)}</small></div></div></td><td>${esc(x.periode_debut || "—")} → ${esc(x.periode_fin || "—")}</td><td>${esc(x.format)}</td><td>${x.demandeur_id && String(x.demandeur_id) === String(me?.id) ? "Vous" : "Personnel HAUQE"}</td><td>${esc(x.date_generation || x.date_demande || "—")}</td><td>${x.document_id ? "Fichier conservé" : "—"}</td><td><span class="report-ready">${statusFr(x.statut)}</span></td><td>${x.document_id && String(x.code_modele).startsWith("BNEC_") ? `<button type="button" class="btn btn-outline-secondary app-btn" data-bnec-download="${esc(x.id)}" data-format="${esc(x.format)}" data-file-base="${esc(`${x.code_modele}-${x.periode_debut}`)}" title="Télécharger ce rapport"><i data-lucide="download"></i>Télécharger</button>` : ""}</td></tr>`).join("") : `<tr><td colspan="8" class="text-center py-4">Aucun rapport demandé.</td></tr>`;
    $("#reportHistoryRows").querySelectorAll("[data-bnec-download]").forEach((button) => button.addEventListener("click", async () => {
      button.disabled = true;
      try { await downloadBnecReport(button.dataset.bnecDownload, button.dataset.format, button.dataset.fileBase); }
      catch (error) { toast(error.message, true); }
      finally { button.disabled = false; }
    }));
    icons();
  }
  async function loadHistory() {
    const payload = await api.apiRequest("/api/v1/reports?limit=100&offset=0"); history = (payload.items || []).filter((item) => item.statut !== "CONFIGURATION"); renderHistory();
    $("#reportKpis").innerHTML = [
      ["green", "file-check-2", "Rapports récents", history.length, "Hors configurations"],
      ["blue", "clock-3", "Générés", history.filter((x) => x.statut === "GENERE").length, "Documents finalisés"],
      ["orange", "loader-circle", "Demandés", history.filter((x) => x.statut === "DEMANDE").length, "En attente"],
      ["purple", "file-spreadsheet", "Formats", "3", "PDF, Excel et CSV"],
    ].map((x) => `<article class="report-kpi ${x[0]}"><span><i data-lucide="${x[1]}"></i></span><div><small>${x[2]}</small><strong>${x[3]}</strong><em>${x[4]}</em></div></article>`).join(""); icons();
  }
  function renderSavedConfigurations() {
    const panel = $("#savedReportConfigurations");
    const items = [...savedConfigurations.entries()];
    panel.innerHTML = `<header><div><h2>Mes configurations enregistrées</h2><p>Un réglage personnel par modèle d’export.</p></div></header><div class="saved-report-list">${items.length ? items.map(([id, config]) => `<button type="button" data-load-report="${esc(id)}"><i data-lucide="folder-open"></i><span>${esc(config.nom_modele || reports.find((report) => report.id === id)?.title || id)}</span><small>Charger</small></button>`).join("") : "Aucune configuration enregistrée."}</div>`;
    panel.querySelectorAll("[data-load-report]").forEach((button) => button.addEventListener("click", () => {
      selected = reports.find((report) => report.id === button.dataset.loadReport) || selected;
      renderList(); renderBuilder();
      panel.hidden = true;
      document.querySelector(".report-builder")?.scrollIntoView({ behavior: "smooth" });
      toast(`Configuration « ${selected.title} » chargée.`);
    }));
    icons();
  }
  async function loadSavedConfigurations() {
    const payload = await api.apiGet("/api/v1/reports/configurations");
    savedConfigurations.clear();
    for (const item of payload.items || []) {
      const id = String(item.code_modele || "").replace(/^EXPORT_CONFIG_/, "").toLowerCase();
      if (reports.some((report) => report.id === id)) savedConfigurations.set(id, item);
    }
    renderSavedConfigurations();
  }
  async function saveReportConfiguration() {
    try {
      if (!selectedSections().size) throw new Error("Sélectionnez au moins une rubrique de contenu.");
      const payload = {
        model_id: selected.id, filtres: selectedExportFilters(),
        sections: { selected: [...selectedSections()] },
        format: document.querySelector('[name="reportFormat"]:checked').value.toUpperCase(),
      };
      const saved = await api.apiRequest("/api/v1/reports/configurations", { method: "POST", body: payload });
      savedConfigurations.set(selected.id, saved);
      renderSavedConfigurations();
      toast(`Configuration « ${selected.title} » enregistrée pour votre compte.`);
    } catch (error) { toast(error.message, true); }
  }
  function csvContent(rows) {
    const flat = rows.map(flatten), headers = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const { start, end } = selectedExportFilters();
    const meta = [
      [institution], [selected.title],
      [`Période filtrée : du ${frDate(start)} au ${frDate(end)} (${exportMeta[selected.id].dateLabel})`],
      [`Généré le ${new Date().toLocaleString("fr-FR")}`],
      [`Demandé par : ${[me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE"}`],
      [`Nombre d’enregistrements : ${rows.length}`], [],
    ];
    return "\ufeff" + [...meta, headers.map(displayKey), ...flat.map((x) => headers.map((h) => x[h] ?? ""))].map((r) => r.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(";")).join("\r\n");
  }
  async function logoDataUrl() {
    const response = await fetch("/static/logo.jpg");
    if (!response.ok) throw new Error("Logo HAUQE indisponible pour le rapport.");
    const reader = new FileReader();
    const loaded = new Promise((resolve, reject) => {
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("Lecture du logo HAUQE impossible."));
    });
    reader.readAsDataURL(await response.blob());
    return loaded;
  }

  async function excelContent(rows) {
    const logo = await logoDataUrl();
    const flat = rows.map(flatten), headers = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const { start, end } = selectedExportFilters();
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    const emptyRow = `<tr><td colspan="${Math.max(headers.length, 1)}">Aucune donnée disponible pour les critères sélectionnés.</td></tr>`;
    return `<!doctype html><html><head><meta charset="utf-8"><style>
      body{margin:20px;font-family:Calibri,Arial,sans-serif;color:#183b2d}
      .institution{display:flex;align-items:center;padding:16px 18px;background:#125f43;color:#fff;border-bottom:5px solid #e4c65e}
      .brand{font-size:24px;font-weight:800}.definition{margin-top:3px;font-size:12px;color:#d9eee5}
      .title{padding:18px;background:#edf7f2;border-left:6px solid #1f7a58}
      .title h1{margin:0 0 5px;font-size:20px;color:#124d38}.title p{margin:0;color:#5b7167;font-size:11px}
      .meta{margin:14px 0;padding:10px 12px;background:#f7faf8;border:1px solid #d9e7e0;font-size:11px}
      table{width:100%;border-collapse:collapse;table-layout:auto;font-size:10px}
      th{padding:10px 8px;background:#176b4d;color:#fff;border:1px solid #0f593f;font-weight:700;text-align:left;vertical-align:middle}
      td{max-width:260px;padding:8px;border:1px solid #d4e2db;vertical-align:top;white-space:normal;word-wrap:break-word}
      tbody tr:nth-child(even) td{background:#eef7f2}
      tbody tr:nth-child(odd) td{background:#fff}
      .footer{margin-top:14px;padding-top:8px;border-top:2px solid #176b4d;color:#687d74;font-size:9px}
    </style></head><body>
      <div class="institution"><img src="${logo}" alt="Logo HAUQE" style="width:58px;height:58px;object-fit:contain;margin-right:10px"><div><div class="brand">HAUQE</div><div class="definition">Haute Autorité de la Qualité et de l’Environnement</div></div></div>
      <div class="title"><h1>${esc(selected.title)}</h1><p>Rapport institutionnel · ${esc(selected.category)}</p></div>
      <div class="meta"><strong>Période filtrée :</strong> du ${esc(frDate(start))} au ${esc(frDate(end))} (${esc(exportMeta[selected.id].dateLabel)})<br><strong>Généré le :</strong> ${esc(new Date().toLocaleString("fr-FR"))}<br><strong>Demandé par :</strong> ${esc(agent)}<br><strong>Nombre d’enregistrements :</strong> ${rows.length}</div>
      <table><thead><tr>${headers.map((h) => `<th>${esc(displayKey(h))}</th>`).join("")}</tr></thead><tbody>${flat.length ? flat.map((x) => `<tr>${headers.map((h) => `<td>${esc(x[h] ?? "")}</td>`).join("")}</tr>`).join("") : emptyRow}</tbody></table>
      <div class="footer">HAUQE Certif · Système national de gestion des certifications</div>
    </body></html>`;
  }
  async function pdfLogoPixels() {
    const image = new Image();
    image.src = "/static/logo.jpg";
    await image.decode();
    const canvas = document.createElement("canvas");
    canvas.width = 64; canvas.height = 64;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.fillStyle = "#fff";
    context.fillRect(0, 0, 64, 64);
    context.drawImage(image, 0, 0, 64, 64);
    const pixels = context.getImageData(0, 0, 64, 64).data;
    let hex = "";
    for (let index = 0; index < pixels.length; index += 4) {
      hex += [pixels[index], pixels[index + 1], pixels[index + 2]]
        .map((value) => value.toString(16).padStart(2, "0")).join("");
    }
    return `${hex}>`;
  }

  async function pdfContent(rows) {
    const logoStream = await pdfLogoPixels();
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    const { start, end } = selectedExportFilters();
    const latin = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\x20-\x7E]/g, "?").replace(/([\\()])/g, "\\$1");
    const flat = rows.map(flatten);
    const allHeaders = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const headers = allHeaders.slice(0, 7);
    if (!headers.length) headers.push("information");
    const pageWidth = 842, margin = 32, tableWidth = pageWidth - margin * 2;
    const colWidth = tableWidth / headers.length, rowHeight = 24, rowsPerPage = 20;
    const pages = Math.max(1, Math.ceil(flat.length / rowsPerPage));
    const logoId = 4 + pages * 2;
    const objects = [null, null];
    const pageIds = [], contentIds = [];
    const fontId = 3;
    objects[fontId - 1] = `${fontId} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n`;
    const text = (value, x, y, size = 8, bold = false) => `BT /F1 ${size} Tf ${x} ${y} Td (${latin(value)}) Tj ET`;
    const maxChars = Math.max(8, Math.floor(colWidth / 4.6));
    for (let pageIndex = 0; pageIndex < pages; pageIndex += 1) {
      const pageId = 4 + pageIndex * 2, contentId = pageId + 1;
      pageIds.push(pageId); contentIds.push(contentId);
      const commands = [
        "0.070 0.373 0.263 rg 0 532 842 63 re f",
        "0.894 0.776 0.369 rg 0 527 842 5 re f",
        "q 52 0 0 52 32 538 cm /Im1 Do Q",
        "1 1 1 rg", text("HAUQE", 95, 568, 22), text("Haute Autorite de la Qualite et de l'Environnement", 95, 548, 9),
        "0.075 0.302 0.220 rg", text(selected.title, 32, 500, 18),
        "0.35 0.44 0.40 rg", text(`Rapport institutionnel | ${selected.category}`, 32, 483, 9),
        text(`Du ${frDate(start)} au ${frDate(end)} | Genere le ${new Date().toLocaleString("fr-FR")} | ${rows.length} enregistrement(s)`, 32, 465, 8),
      ];
      let y = 432;
      commands.push("0.090 0.420 0.302 rg", `${margin} ${y} ${tableWidth} ${rowHeight} re f`);
      headers.forEach((header, index) => {
        commands.push("1 1 1 rg", text(displayKey(header).slice(0, maxChars), margin + index * colWidth + 5, y + 8, 7));
        commands.push("0.72 0.82 0.77 RG 0.45 w", `${margin + index * colWidth} ${y} ${colWidth} ${rowHeight} re S`);
      });
      const pageRows = flat.slice(pageIndex * rowsPerPage, (pageIndex + 1) * rowsPerPage);
      if (!pageRows.length) pageRows.push({ information: "Aucune donnee disponible pour les criteres selectionnes." });
      pageRows.forEach((row, rowIndex) => {
        y -= rowHeight;
        commands.push(rowIndex % 2 ? "0.930 0.970 0.950 rg" : "1 1 1 rg", `${margin} ${y} ${tableWidth} ${rowHeight} re f`);
        headers.forEach((header, index) => {
          const raw = String(row[header] ?? "");
          const value = raw.length > maxChars ? `${raw.slice(0, maxChars - 1)}…` : raw;
          commands.push("0.13 0.24 0.19 rg", text(value, margin + index * colWidth + 5, y + 8, 7));
          commands.push("0.80 0.87 0.83 RG 0.35 w", `${margin + index * colWidth} ${y} ${colWidth} ${rowHeight} re S`);
        });
      });
      commands.push("0.35 0.44 0.40 rg", text(`HAUQE Certif | Page ${pageIndex + 1} / ${pages}`, 32, 22, 7));
      const stream = commands.join("\n");
      objects[pageId - 1] = `${pageId} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 ${fontId} 0 R >> /XObject << /Im1 ${logoId} 0 R >> >> /Contents ${contentId} 0 R >> endobj\n`;
      objects[contentId - 1] = `${contentId} 0 obj << /Length ${stream.length} >> stream\n${stream}\nendstream endobj\n`;
    }
    objects[logoId - 1] = `${logoId} 0 obj << /Type /XObject /Subtype /Image /Width 64 /Height 64 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /ASCIIHexDecode /Length ${logoStream.length} >> stream\n${logoStream}\nendstream endobj\n`;
    objects[0] = "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n";
    objects[1] = `2 0 obj << /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pages} >> endobj\n`;
    let pdf = "%PDF-1.4\n", offsets = [0];
    objects.forEach((object) => { offsets.push(pdf.length); pdf += object; });
    const objectCount = objects.length + 1;
    const xref = pdf.length;
    pdf += `xref\n0 ${objectCount}\n0000000000 65535 f \n${offsets.slice(1).map((n) => String(n).padStart(10, "0") + " 00000 n \n").join("")}trailer << /Size ${objectCount} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
    return pdf;
  }
  function download(content, filename, type) {
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([content], { type })); a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  async function downloadBnecReport(id, format, fileBase = `rapport-bnec-${id}`) {
    const blob = await api.apiBlob(`/api/v1/reports/${encodeURIComponent(id)}/download`, { timeoutMs: 120000 });
    const extension = { PDF: "pdf", XLSX: "xlsx", CSV: "csv" }[String(format).toUpperCase()] || "dat";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = `${String(fileBase).toLowerCase().replace(/[^a-z0-9-]+/g, '-')}.${extension}`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function bnecSelection() {
    const year = Number($("#bnecReportYear").value);
    const month = Number($("#bnecReportMonth").value);
    const quarter = Number($("#bnecReportQuarter").value);
    if (!Number.isInteger(year) || year < 2000 || year > 2100) throw new Error("Choisissez une année valide.");
    return { type: bnecType, year, month: bnecType === "MENSUEL" ? month : null, quarter: bnecType === "TRIMESTRIEL" ? quarter : null };
  }
  function chooseBnecType(type) {
    if (!["MENSUEL", "TRIMESTRIEL", "ANNUEL"].includes(type)) return;
    bnecType = type;
    document.querySelectorAll("[data-bnec-type]").forEach((button) => {
      button.classList.toggle("active", button.dataset.bnecType === type);
      button.setAttribute("aria-pressed", String(button.dataset.bnecType === type));
    });
    $("#bnecReportMonthField").hidden = type !== "MENSUEL";
    $("#bnecReportQuarterField").hidden = type !== "TRIMESTRIEL";
    clearBnecPreview();
  }
  function clearBnecPreview() {
    previewRequestId += 1;
    previewPendingKey = null;
    $("#bnecReportPreviewPanel").hidden = true;
    $("#bnecReportPreview").removeAttribute("aria-busy");
  }
  async function previewBnec() {
    const button = $("#bnecReportPreview"), panel = $("#bnecReportPreviewPanel");
    let requestId = 0;
    try {
      const selection = bnecSelection();
      const key = JSON.stringify(selection);
      if (previewPendingKey === key) {
        panel.hidden = false;
        return;
      }
      requestId = ++previewRequestId;
      previewPendingKey = key;
      button.setAttribute("aria-busy", "true");
      panel.innerHTML = "<strong>Calcul de l’aperçu en cours…</strong><p>Les indicateurs sont recalculés pour la période sélectionnée.</p>";
      panel.hidden = false;
      const query = new URLSearchParams({ type: selection.type, year: String(selection.year) });
      if (selection.month) query.set("month", String(selection.month));
      if (selection.quarter) query.set("quarter", String(selection.quarter));
      const preview = await api.apiGet(`/api/v1/reports/bnec/preview?${query}`, { timeoutMs: 120000 });
      if (requestId !== previewRequestId) return;
      panel.innerHTML = `<strong>${esc(preview.title)} — ${esc(preview.period_label)}</strong><p>Période du ${esc(frDate(preview.start))} au ${esc(frDate(preview.end))}. ${preview.provisional ? `Bilan provisoire : données arrêtées au ${esc(frDate(preview.data_as_of))}.` : "Période achevée."} ${preview.rows.length} élément(s) expliqués à partir des calculs du serveur.</p><p>${esc(preview.methodology || "")}</p><div class="bnec-preview-rows">${preview.rows.slice(0, 18).map(([label, value]) => `<div><span>${esc(label)}</span><b>${esc(value)}</b></div>`).join("")}</div>${preview.rows.length > 18 ? `<small>Aperçu limité à 18 éléments ; le rapport complet conservera toutes les explications.</small>` : ""}`;
      panel.hidden = false;
    } catch (error) {
      if (!requestId || requestId === previewRequestId) {
        panel.textContent = error?.message || "Impossible de calculer l’aperçu.";
        panel.hidden = false;
        toast(panel.textContent, true);
      }
    } finally {
      if (requestId && requestId === previewRequestId) {
        previewPendingKey = null;
        button.removeAttribute("aria-busy");
      }
    }
  }
  async function generateBnec() {
    const button = $("#bnecReportGenerate");
    button.disabled = true;
    try {
      const selection = bnecSelection();
      const result = await api.apiRequest("/api/v1/reports/bnec/generate", { method: "POST", body: { ...selection, format: $("#bnecReportFormat").value }, timeoutMs: 120000 });
      await downloadBnecReport(result.id, result.format, `${result.code_modele}-${result.periode_debut}`);
      await loadHistory();
      toast("Bilan BNEC généré, téléchargé et conservé dans l’historique.");
    } catch (error) { toast(error.message, true); }
    finally { button.disabled = false; }
  }
  async function generate() {
    const format = document.querySelector('[name="reportFormat"]:checked').value.toUpperCase();
    try {
      currentRows = (await loadFilteredExport()).rows;
      const base = `${selected.id}-${new Date().toISOString().slice(0, 10)}`;
      if (format === "CSV") download(csvContent(currentRows), `${base}.csv`, "text/csv;charset=utf-8");
      else if (format === "XLSX") download(await excelContent(currentRows), `${base}.xls`, "application/vnd.ms-excel");
      else download(await pdfContent(currentRows), `${base}.pdf`, "application/pdf");
      toast(`Export instantané téléchargé (${currentRows.length} ligne(s)). Il n'est pas archivé comme bilan BNEC.`);
    } catch (error) { toast(error.message, true); }
  }
  async function preview() {
    try {
      currentRows = (await loadFilteredExport()).rows;
    } catch (error) {
      toast(error.message, true);
      return;
    }
    const previewRows = currentRows.slice(0, 6).map(flatten);
    const headers = [...new Set(previewRows.flatMap((row) => Object.keys(row)))].slice(0, 5);
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    $("#previewTitle").textContent = selected.title; $("#paperTitle").textContent = selected.title;
    const { start, end } = selectedExportFilters();
    $("#paperPeriod").textContent = `${selected.category} · Du ${frDate(start)} au ${frDate(end)} · Source HAUQE Certif`;
    $("#paperReportMeta").innerHTML = `<span><small>Généré le</small><strong>${esc(new Date().toLocaleString("fr-FR"))}</strong></span><span><small>Demandé par</small><strong>${esc(agent)}</strong></span><span><small>Enregistrements</small><strong>${currentRows.length}</strong></span>`;
    $("#paperTable").innerHTML = headers.length
      ? `<table><thead><tr>${headers.map((h) => `<th>${esc(displayKey(h))}</th>`).join("")}</tr></thead><tbody>${previewRows.map((row) => `<tr>${headers.map((h) => `<td>${esc(row[h] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table>${currentRows.length > 6 ? `<p class="paper-table-note">Aperçu limité à 6 lignes sur ${currentRows.length}. Le document généré contiendra toutes les données.</p>` : ""}`
      : `<div class="paper-empty">Aucune donnée disponible pour les critères sélectionnés.</div>`;
    $("#reportPreview").hidden = false; icons();
  }
  $("#reportSearch").oninput = renderList; $("#historySearch").oninput = renderHistory;
  $("#reportPeriod").onchange = (e) => $("#customDates").hidden = e.target.value !== "custom";
  document.querySelectorAll('[name="reportFormat"]').forEach((r) => r.onchange = () => document.querySelectorAll(".format-options>label").forEach((l) => l.classList.toggle("selected", l.contains(r) && r.checked)));
  $("#generateReport").onclick = generate; $("#generateFromPreview").onclick = async () => { $("#reportPreview").hidden = true; await generate(); };
  $("#previewReport").onclick = preview; $("#closePreview").onclick = $("#closePreviewFooter").onclick = () => $("#reportPreview").hidden = true;
  $("#saveReportConfig").onclick = saveReportConfiguration;
  $("#savedReports").onclick = () => {
    const panel = $("#savedReportConfigurations");
    panel.hidden = !panel.hidden;
    if (!panel.hidden) panel.scrollIntoView({ behavior: "smooth" });
  };
  $("#customReport").hidden = true; $("#favoriteReport").hidden = true;
  $("#bnecReportPreview").lastChild.textContent = "Aperçu du bilan BNEC";
  const now = new Date();
  document.querySelector('#reportPeriod option[value="year"]').textContent = `Année ${now.getFullYear()}`;
  $("#bnecReportYear").value = String(now.getFullYear());
  $("#bnecReportMonth").innerHTML = Array.from({ length: 12 }, (_, i) => `<option value="${i + 1}">${new Intl.DateTimeFormat("fr-FR", { month: "long" }).format(new Date(2020, i, 1))}</option>`).join("");
  $("#bnecReportMonth").value = String(now.getMonth() + 1);
  $("#bnecReportQuarter").value = String(Math.ceil((now.getMonth() + 1) / 3));
  document.querySelectorAll("[data-bnec-type]").forEach((button) => button.addEventListener("click", () => chooseBnecType(button.dataset.bnecType)));
  ["#bnecReportYear", "#bnecReportMonth", "#bnecReportQuarter"].forEach((selector) => $(selector).addEventListener("change", clearBnecPreview));
  $("#bnecReportPreview").addEventListener("click", previewBnec);
  $("#bnecReportGenerate").addEventListener("click", generateBnec);
  const incoming = new URLSearchParams(location.hash.split("?")[1] || "");
  if (incoming.has("year")) $("#bnecReportYear").value = incoming.get("year");
  if (incoming.has("month")) $("#bnecReportMonth").value = incoming.get("month");
  if (incoming.has("quarter")) $("#bnecReportQuarter").value = incoming.get("quarter");
  chooseBnecType(incoming.get("type") || "MENSUEL");
  renderCategories(); renderList(); renderBuilder();
  try { me = await api.apiRequest("/api/v1/me"); await loadSavedConfigurations(); renderBuilder(); await loadHistory(); } catch (error) { toast(error.message, true); }
})();
