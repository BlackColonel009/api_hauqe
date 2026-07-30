(async function () {
  "use strict";
  const api = await import("/static/js/core/api.js");
  const $ = (s) => document.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
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
  function toast(message, error = false) { const b = $("#reportToast"); b.querySelector("span").textContent = message; b.classList.toggle("error", error); b.hidden = false; setTimeout(() => b.hidden = true, 2800); }
  const normalize = (payload) => Array.isArray(payload) ? payload : (payload?.items || payload?.results || payload?.data || []);
  async function loadAllRows(baseUrl) {
    const collected = []; let offset = 0;
    for (let page = 0; page < 100; page += 1) {
      const join = baseUrl.includes("?") ? "&" : "?";
      const payload = await api.apiRequest(`${baseUrl}${join}limit=100&offset=${offset}`);
      const rows = normalize(payload); collected.push(...rows);
      const total = Number(payload?.total ?? rows.length);
      if (!rows.length || collected.length >= total || rows.length < 100) break;
      offset += rows.length;
    }
    return collected;
  }
  const scalar = (v) => v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v);
  function flatten(row) {
    const out = {};
    Object.entries(row || {}).forEach(([k, v]) => {
      if (["created_at", "updated_at"].includes(k) || Array.isArray(v)) return;
      out[k.replaceAll("_", " ")] = scalar(v);
    });
    return out;
  }
  function displayKey(key) { return key.replace(/^\p{L}/u, (c) => c.toUpperCase()); }
  function periodDates() {
    const now = new Date(), mode = $("#reportPeriod").value;
    let start, end = now.toISOString().slice(0, 10);
    if (mode === "month") start = `${end.slice(0, 8)}01`;
    else if (mode === "quarter") start = `${now.getFullYear()}-${String(Math.floor(now.getMonth() / 3) * 3 + 1).padStart(2, "0")}-01`;
    else if (mode === "year") start = `${now.getFullYear()}-01-01`;
    else { start = $("#reportStart").value || null; end = $("#reportEnd").value || null; }
    return { start, end };
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
    $("#reportOptions").innerHTML = ["Identifiants et références", "Statuts et résultats", "Dates et échéances", "Données détaillées"].map((x) => `<label class="report-option"><input type="checkbox" checked>${x}</label>`).join(""); icons();
  }
  function statusFr(v) {
    const s = String(v || "DEMANDE").toUpperCase();
    return ({ DEMANDE: "Demandé", EN_GENERATION: "En génération", GENERE: "Généré", ECHEC: "Échec" })[s] || s.replaceAll("_", " ");
  }
  function renderHistory() {
    const q = $("#historySearch").value.toLowerCase();
    const rows = history.filter((x) => `${x.nom_modele} ${x.categorie} ${x.format}`.toLowerCase().includes(q));
    $("#reportHistoryRows").innerHTML = rows.length ? rows.map((x) => `<tr><td><div class="history-report"><span class="${String(x.format).toLowerCase()}"><i data-lucide="file-text"></i></span><div><strong>${esc(x.nom_modele)}</strong><small>${esc(x.code_modele)}</small></div></div></td><td>${esc(x.periode_debut || "—")} → ${esc(x.periode_fin || "—")}</td><td>${esc(x.format)}</td><td>${esc(String(x.demandeur_id).slice(0, 8))}</td><td>${esc(x.date_generation || x.date_demande || "—")}</td><td>—</td><td><span class="report-ready">${statusFr(x.statut)}</span></td><td></td></tr>`).join("") : `<tr><td colspan="8" class="text-center py-4">Aucun rapport demandé.</td></tr>`; icons();
  }
  async function loadHistory() {
    const payload = await api.apiRequest("/api/v1/reports?limit=100&offset=0"); history = payload.items || []; renderHistory();
    $("#reportKpis").innerHTML = [
      ["green", "file-check-2", "Rapports enregistrés", payload.total || 0, "Historique serveur"],
      ["blue", "clock-3", "Générés", history.filter((x) => x.statut === "GENERE").length, "Documents finalisés"],
      ["orange", "loader-circle", "Demandés", history.filter((x) => x.statut === "DEMANDE").length, "En attente"],
      ["purple", "file-spreadsheet", "Formats", "3", "PDF, Excel et CSV"],
    ].map((x) => `<article class="report-kpi ${x[0]}"><span><i data-lucide="${x[1]}"></i></span><div><small>${x[2]}</small><strong>${x[3]}</strong><em>${x[4]}</em></div></article>`).join(""); icons();
  }
  function csvContent(rows) {
    const flat = rows.map(flatten), headers = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const meta = [
      [institution], [selected.title],
      [`Généré le ${new Date().toLocaleString("fr-FR")}`],
      [`Demandé par : ${[me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE"}`],
      [`Nombre d’enregistrements : ${rows.length}`], [],
    ];
    return "\ufeff" + [...meta, headers.map(displayKey), ...flat.map((x) => headers.map((h) => x[h] ?? ""))].map((r) => r.map((v) => `"${String(v).replaceAll('"', '""')}"`).join(";")).join("\r\n");
  }
  function excelContent(rows) {
    const flat = rows.map(flatten), headers = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    const emptyRow = `<tr><td colspan="${Math.max(headers.length, 1)}">Aucune donnée disponible pour les critères sélectionnés.</td></tr>`;
    return `<!doctype html><html><head><meta charset="utf-8"><style>
      body{margin:20px;font-family:Calibri,Arial,sans-serif;color:#183b2d}
      .institution{padding:16px 18px;background:#125f43;color:#fff;border-bottom:5px solid #e4c65e}
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
      <div class="institution"><div class="brand">HAUQE</div><div class="definition">Haute Autorité de la Qualité et de l’Environnement</div></div>
      <div class="title"><h1>${esc(selected.title)}</h1><p>Rapport institutionnel · ${esc(selected.category)}</p></div>
      <div class="meta"><strong>Généré le :</strong> ${esc(new Date().toLocaleString("fr-FR"))}<br><strong>Demandé par :</strong> ${esc(agent)}<br><strong>Nombre d’enregistrements :</strong> ${rows.length}</div>
      <table><thead><tr>${headers.map((h) => `<th>${esc(displayKey(h))}</th>`).join("")}</tr></thead><tbody>${flat.length ? flat.map((x) => `<tr>${headers.map((h) => `<td>${esc(x[h] ?? "")}</td>`).join("")}</tr>`).join("") : emptyRow}</tbody></table>
      <div class="footer">HAUQE Certif · Système national de gestion des certifications</div>
    </body></html>`;
  }
  function pdfContent(rows) {
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    const latin = (s) => String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\x20-\x7E]/g, "?").replace(/([\\()])/g, "\\$1");
    const flat = rows.map(flatten);
    const allHeaders = [...new Set(flat.flatMap((x) => Object.keys(x)))];
    const headers = allHeaders.slice(0, 7);
    if (!headers.length) headers.push("information");
    const pageWidth = 842, margin = 32, tableWidth = pageWidth - margin * 2;
    const colWidth = tableWidth / headers.length, rowHeight = 24, rowsPerPage = 20;
    const pages = Math.max(1, Math.ceil(flat.length / rowsPerPage));
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
        "1 1 1 rg", text("HAUQE", 32, 568, 22), text("Haute Autorite de la Qualite et de l'Environnement", 32, 548, 9),
        "0.075 0.302 0.220 rg", text(selected.title, 32, 500, 18),
        "0.35 0.44 0.40 rg", text(`Rapport institutionnel | ${selected.category}`, 32, 483, 9),
        text(`Genere le ${new Date().toLocaleString("fr-FR")} | Demande par : ${agent} | ${rows.length} enregistrement(s)`, 32, 465, 8),
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
      objects[pageId - 1] = `${pageId} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >> endobj\n`;
      objects[contentId - 1] = `${contentId} 0 obj << /Length ${stream.length} >> stream\n${stream}\nendstream endobj\n`;
    }
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
  async function generate() {
    const format = document.querySelector('[name="reportFormat"]:checked').value.toUpperCase();
    const { start, end } = periodDates();
    try {
      currentRows = await loadAllRows(selected.url);
      await api.apiRequest("/api/v1/reports", { method: "POST", body: {
        code_modele: selected.id, nom_modele: selected.title, categorie: selected.category,
        filtres: { region: $("#reportRegion").value, statut: $("#reportStatus").value },
        sections: { donnees_detaillees: true }, format: format === "XLSX" ? "XLSX" : format,
        periode_debut: start, periode_fin: end,
      } });
      const base = `${selected.id}-${new Date().toISOString().slice(0, 10)}`;
      if (format === "CSV") download(csvContent(currentRows), `${base}.csv`, "text/csv;charset=utf-8");
      else if (format === "XLSX") download(excelContent(currentRows), `${base}.xls`, "application/vnd.ms-excel");
      else download(pdfContent(currentRows), `${base}.pdf`, "application/pdf");
      toast(`${selected.title} téléchargé en ${format === "XLSX" ? "Excel" : format} (${currentRows.length} ligne(s)).`);
      await loadHistory();
    } catch (error) { toast(error.message, true); }
  }
  async function preview() {
    try {
      currentRows = await loadAllRows(selected.url);
    } catch (error) {
      toast(error.message, true);
      return;
    }
    const previewRows = currentRows.slice(0, 6).map(flatten);
    const headers = [...new Set(previewRows.flatMap((row) => Object.keys(row)))].slice(0, 5);
    const agent = [me?.prenoms, me?.nom].filter(Boolean).join(" ") || me?.email || "Agent HAUQE";
    $("#previewTitle").textContent = selected.title; $("#paperTitle").textContent = selected.title;
    $("#paperPeriod").textContent = `${selected.category} · Source officielle HAUQE Certif`;
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
  $("#saveReportConfig").onclick = () => toast("La configuration sera enregistrée lors de la génération.");
  $("#savedReports").onclick = () => document.querySelector(".report-history")?.scrollIntoView({ behavior: "smooth" });
  $("#customReport").hidden = true; $("#favoriteReport").hidden = true;
  renderCategories(); renderList(); renderBuilder();
  try { me = await api.apiRequest("/api/v1/me"); await loadHistory(); } catch (error) { toast(error.message, true); }
})();
