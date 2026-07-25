window.HAUQE_MOCK = {
  metrics: [
    { label: "Entreprises enregistrées", value: 128, delta: "+8,5 %", trend: "up", icon: "building-2", tone: "green", note: "10 nouvelles cette année" },
    { label: "Certifications actives", value: 174, delta: "+5,2 %", trend: "up", icon: "badge-check", tone: "blue", note: "sur 212 certifications" },
    { label: "Entreprises à risque", value: 19, delta: "+3", trend: "alert", icon: "triangle-alert", tone: "orange", note: "à contrôler en priorité" },
    { label: "Contrôles à planifier", value: 14, delta: "6 urgents", trend: "alert", icon: "clipboard-clock", tone: "purple", note: "dans les 30 prochains jours" }
  ],
  statuses: [
    { label: "Valides", value: 174, color: "#178a60" },
    { label: "À vérifier", value: 17, color: "#f2a53b" },
    { label: "Expirées", value: 13, color: "#dc5a55" },
    { label: "Suspendues", value: 8, color: "#7e8698" }
  ],
  activity: {
    labels: ["Fév.", "Mars", "Avr.", "Mai", "Juin", "Juil."],
    active: [144, 151, 149, 160, 166, 174],
    renewed: [8, 12, 9, 16, 14, 18],
    expired: [5, 7, 6, 8, 10, 7]
  },
  priorities: [
    { level: "critical", title: "5 certificats expirent sous 30 jours", meta: "Action immédiate requise", icon: "siren" },
    { level: "warning", title: "4 fiches attendent une validation", meta: "Depuis plus de 48 heures", icon: "file-clock" },
    { level: "info", title: "3 contrôles HAUQE sont en retard", meta: "Responsables à relancer", icon: "calendar-x-2" }
  ],
  recent: [
    { initials: "AV", company: "AGROVITA SARL", sector: "Agroalimentaire", certification: "ISO 22000", code: "TG-AGRO-ISO22000-2025-014", body: "Bureau Veritas", expiry: "03 août 2026", days: "18 jours", status: "À surveiller", statusTone: "warning", score: 82 },
    { initials: "KT", company: "KATIO FOODS", sector: "Transformation", certification: "HACCP", code: "TG-AGRO-HACCP-2026-022", body: "SGS Togo", expiry: "18 mars 2027", days: "245 jours", status: "Valide", statusTone: "success", score: 91 },
    { initials: "DN", company: "DÉLICES DU NORD", sector: "Agroalimentaire", certification: "COTAG ARS 466", code: "TGN/COTAG/084/DG/2025", body: "ATN / COTAG", expiry: "11 nov. 2026", days: "118 jours", status: "À vérifier", statusTone: "neutral", score: 64 },
    { initials: "TF", company: "TOGO FRESH EXPORT", sector: "Exportation", certification: "BIO", code: "TG-AGRO-BIO-2025-008", body: "Ecocert", expiry: "28 sept. 2026", days: "74 jours", status: "Valide", statusTone: "success", score: 88 }
  ]
};
