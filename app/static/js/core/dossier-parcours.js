import { apiGet as defaultApiGet } from "./api.js?v=20260927-1";

const DOSSIER_PARCOURS_EVENT = "hauqe:dossier-parcours-changed";
const registeredParcours = new Map();
let refreshScheduled = false;

const ICONS = {
  COLLECTE: "clipboard-check",
  VERIFICATION: "file-search",
  FUCCS: "shield-check",
  N1: "badge-1",
  N2: "badge-2",
  BNEC: "database-zap",
};

const LABELS = {
  TERMINE: "Terminée",
  EN_COURS: "En cours",
  A_FAIRE: "À faire",
  BLOQUE: "Bloquée",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export async function renderDossierParcours({ target, source, resourceId, apiGet = defaultApiGet }) {
  const container = typeof target === "string" ? document.querySelector(target) : target;
  if (!container || !resourceId) return;

  registeredParcours.set(container, { source, resourceId, apiGet });

  try {
    const parcours = await apiGet(
      `/api/v1/parcours-dossier/${encodeURIComponent(source)}/${encodeURIComponent(resourceId)}`
    );
    const remaining = Number(parcours.etapes_restantes || 0);
    container.hidden = false;
    container.innerHTML = `
      <div class="dossier-parcours-heading">
        <div>
          <p class="eyebrow">Suivi du dossier</p>
          <h2>Parcours de traitement</h2>
          <p>${escapeHtml(parcours.prochaine_action || "Parcours en cours de mise à jour.")}</p>
        </div>
        <span class="dossier-parcours-count ${parcours.bloque ? "blocked" : ""}">
          ${parcours.bloque ? "Action requise" : remaining ? `${remaining} étape${remaining > 1 ? "s" : ""} restante${remaining > 1 ? "s" : ""}` : "Parcours terminé"}
        </span>
      </div>
      <ol class="dossier-parcours-steps">
        ${(parcours.etapes || []).map((step, index) => `
          <li class="${String(step.statut || "A_FAIRE").toLowerCase()}">
            <span class="dossier-parcours-marker">${index + 1}</span>
            <div class="dossier-parcours-icon"><i data-lucide="${ICONS[step.code] || "circle"}"></i></div>
            <div class="dossier-parcours-copy">
              <strong>${escapeHtml(step.libelle)}</strong>
              <small>${escapeHtml(step.detail)}</small>
            </div>
            <em>${escapeHtml(LABELS[step.statut] || step.statut)}</em>
          </li>
        `).join("")}
      </ol>
    `;
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  } catch (error) {
    // Le parcours est une aide de lecture : il ne doit jamais empêcher la fiche principale de fonctionner.
    container.hidden = true;
  }
}

async function refreshRegisteredParcours() {
  refreshScheduled = false;
  const refreshes = [];
  for (const [container, options] of registeredParcours.entries()) {
    if (!document.contains(container)) {
      registeredParcours.delete(container);
      continue;
    }
    refreshes.push(renderDossierParcours({ target: container, ...options }));
  }
  await Promise.allSettled(refreshes);
}

if (typeof window !== "undefined") {
  window.addEventListener(DOSSIER_PARCOURS_EVENT, () => {
    // Plusieurs écritures successives (fiche, offres, certifications…) ne
    // produisent qu'un redessin au cycle suivant.
    if (refreshScheduled) return;
    refreshScheduled = true;
    window.setTimeout(refreshRegisteredParcours, 80);
  });
}
