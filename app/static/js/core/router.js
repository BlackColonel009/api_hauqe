import { APP_CONFIG } from "./config.js";
import { hasAccessToken } from "./api.js";

const routes = Object.freeze({
  dashboard: { view: "/views/dashboard", script: "/static/js/app.js", title: "Tableau de bord" },
  alertes: { view: "/views/alertes", script: "/static/js/alertes.js", title: "Centre des alertes" },
  echeances: { view: "/views/echeances", script: "/static/js/echeances.js", title: "Calendrier des échéances" },
  entreprises: { view: "/views/entreprises", script: "/static/js/entreprises.js", title: "Entreprises certifiées" },
  "entreprise-detail": { view: "/views/entreprise-detail", script: "/static/js/entreprise-detail.js", title: "Dossier entreprise" },
  "entreprise-form": { view: "/views/entreprise-form", script: "/static/js/entreprise-form.js", title: "Entreprise — formulaire" },
  certifications: { view: "/views/certifications", script: "/static/js/certifications.js", title: "Certifications" },
  "certification-detail": { view: "/views/certification-detail", script: "/static/js/certification-detail.js", title: "Dossier certification" },
  "certification-form": { view: "/views/certification-form", script: "/static/js/certification-form.js", title: "Certification — formulaire" },
  organismes: { view: "/views/organismes", script: "/static/js/organismes.js", title: "Organismes certificateurs" },
  "organisme-detail": { view: "/views/organisme-detail", script: "/static/js/organisme-detail.js", title: "Dossier organisme" },
  "organisme-form": { view: "/views/organisme-form", script: "/static/js/organisme-form.js", title: "Organisme — formulaire" },
  collectes: { view: "/views/collectes", script: "/static/js/collectes.js", title: "Collectes & contrôles" },
  "collecte-form": { view: "/views/collecte-form", script: "/static/js/collecte-form.js", title: "Fiche de collecte" },
  validations: { view: "/views/validations", script: "/static/js/validations.js", title: "Validation des collectes" },
  controle: { view: "/views/controle", script: "/static/js/controle.js", title: "Grille de contrôle" },
  "controle-detail": { view: "/views/controle-detail", script: "/static/js/controle-detail.js", title: "Contrôle FUCCS" },
  scoring: { view: "/views/scoring", script: "/static/js/scoring.js", title: "Scoring et conformité" },
  rapports: { view: "/views/rapports", script: "/static/js/rapports.js", title: "Rapports et exports" },
  utilisateurs: { view: "/views/utilisateurs", script: "/static/js/utilisateurs.js", title: "Gestion des utilisateurs" },
  referentiels: { view: "/views/referentiels", script: "/static/js/referentiels.js", title: "Référentiels" },
  "regles-codification": { view: "/views/regles-codification", script: "/static/js/regles-codification.js", title: "Règles et codification" },
  "journal-audit": { view: "/views/journal-audit", script: "/static/js/journal-audit.js", title: "Journal d’audit" },
  connexion: { view: "/views/connexion", script: "/static/js/connexion.js", title: "Connexion" },
  "mot-de-passe-oublie": { view: "/views/mot-de-passe-oublie", script: "/static/js/mot-de-passe-oublie.js", title: "Mot de passe oublié" },
  profil: { view: "/views/profil", script: "/static/js/profil.js", title: "Mon profil" },
  verifications: { view: "/views/verifications", script: "/static/js/verifications.js", title: "Vérification documentaire" },
  "verification-detail": { view: "/views/verification-detail", script: "/static/js/verification-detail.js", title: "Dossier de vérification" },
  integrations: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Intégration BNEC" },
  infc: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "INFC" },
  "classement-sncc": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Classement SNCC" },
  veille: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Cellule de veille" },
  decisions: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Décisions et plans d’action" },
  "mises-a-jour": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Mises à jour BNEC" },
  documents: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Gestion documentaire" },
  incidents: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Incidents" },
  "amelioration-continue": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Amélioration continue" },
  sauvegardes: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Sauvegardes et restaurations" },
  "qualite-donnees": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Qualité des données" },
  publications: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Publications" },
  "echanges-organismes": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Échanges avec les organismes" },
  "tableau-tactique": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Tableau de bord tactique" },
  "tableau-strategique": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Tableau de bord stratégique" },
  "tableau-annuel": { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Tableau de bord annuel" },
  barometre: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Baromètre national" },
  public: { view: "/views/governance-module", script: "/static/js/governance-modules.js", title: "Tableau de bord public" },
});

let currentRoute = null;

function routeName() {
  const parts = location.hash.replace(/^#\/?/, "").split("/");
  const name = parts[0] === "entreprises" && ["nouveau", "modifier"].includes(parts[1]) ? "entreprise-form" : parts[0] === "entreprises" && parts[1] ? "entreprise-detail" : parts[0] === "certifications" && ["nouveau", "modifier"].includes(parts[1]) ? "certification-form" : parts[0] === "certifications" && parts[1] ? "certification-detail" : parts[0] === "organismes" && ["nouveau", "modifier"].includes(parts[1]) ? "organisme-form" : parts[0] === "organismes" && parts[1] ? "organisme-detail" : parts[0] === "collectes" && ["nouveau", "modifier"].includes(parts[1]) ? "collecte-form" : parts[0] === "verifications" && parts[1] ? "verification-detail" : parts[0] === "controle" && parts[1] ? "controle-detail" : parts[0] === "tableaux-de-bord" && parts[1] ? `tableau-${parts[1]}` : parts[0];
  return routes[name] ? name : APP_CONFIG.defaultRoute;
}

function setActiveRoute(name) {
  document.querySelectorAll("[data-route]").forEach((link) => link.classList.toggle("active", link.dataset.route === name));
}

function extractContent(html) {
  const documentFragment = new DOMParser().parseFromString(html, "text/html");
  const page = documentFragment.querySelector(".page-content");
  if (!page) throw new Error("Contenu de page introuvable");
  return page.outerHTML;
}

function executePageScript(src) {
  document.querySelectorAll("script[data-page-script]").forEach((script) => script.remove());
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `${src}?v=${Date.now()}`;
    script.dataset.pageScript = "true";
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}


const PUBLIC_ROUTES = new Set([
  "connexion",
  "mot-de-passe-oublie",
  "public",
]);

function enforceRouteAuthentication(name) {
  if (PUBLIC_ROUTES.has(name)) return true;

  if (!hasAccessToken()) {
    sessionStorage.setItem(
      "hauqe-return-after-login",
      location.hash || "#/dashboard"
    );
    location.hash = "#/connexion";
    return false;
  }

  return true;
}

function applyAuthRouteClass(name) {
  document.body.classList.toggle(
    "auth-route-active",
    ["connexion", "mot-de-passe-oublie"].includes(name)
  );
}

export async function navigate() {
  const loadingStartedAt = performance.now();
  const name = routeName();

  if (!enforceRouteAuthentication(name)) {
    return;
  }

  applyAuthRouteClass(name);

  const route = routes[name];
  const content = document.querySelector("#pageContent");
  const loading = document.querySelector("#routeLoading");
  const error = document.querySelector("#routeError");
  loading.hidden = false; error.hidden = true;
  try {
    const response = await fetch(route.view, { headers: { "X-Requested-With": "HAUQE-SPA" } });
    if (!response.ok) throw new Error(`Erreur ${response.status}`);
    content.innerHTML = extractContent(await response.text());
    await executePageScript(route.script);
    window.dispatchEvent(new CustomEvent("hauqe:page-ready", { detail: { route: name } }));
    currentRoute = name;
    setActiveRoute(name);
    document.title = `${APP_CONFIG.appName} — ${route.title}`;
    document.querySelector("#sidebar").classList.remove("open");
    window.scrollTo({ top: 0, behavior: "instant" });
    if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  } catch (err) {
    console.error(err); content.innerHTML = ""; error.hidden = false;
  } finally { const remaining=420-(performance.now()-loadingStartedAt);if(remaining>0)await new Promise(resolve=>setTimeout(resolve,remaining));loading.hidden=true; }
}

export function initRouter() {
  window.addEventListener("hashchange", navigate);
  document.querySelector("#retryRoute").addEventListener("click", navigate);
  if (!location.hash) location.replace(`#/${APP_CONFIG.defaultRoute}`); else navigate();
}

export function getCurrentRoute() { return currentRoute; }
