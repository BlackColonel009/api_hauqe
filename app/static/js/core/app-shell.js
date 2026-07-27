import { initRouter } from "./router.js";
import { initSessionLock } from "./session-lock.js";
import {
  getCurrentProfile,
  logout,
} from "./auth.js";
import { apiBlob, hasAccessToken } from "./api.js";

document.querySelector("#menuToggle").addEventListener("click", () => document.querySelector("#sidebar").classList.toggle("open"));
document.addEventListener("click", (event) => {
  const disabledLink = event.target.closest(".nav-link.disabled");
  if (disabledLink) event.preventDefault();
});

const notificationToggle = document.querySelector("#notificationToggle");
const notificationDropdown = document.querySelector("#notificationDropdown");
const userMenuToggle = document.querySelector("#userMenuToggle");
const accountDropdown = document.querySelector("#accountDropdown");
const themeSwitch = document.querySelector("#themeSwitch");
const themeSwitchLabel = document.querySelector("#themeSwitchLabel");
function applyTheme(theme) {
  const dark = theme === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  themeSwitch.setAttribute("aria-checked", String(dark));
  themeSwitch.setAttribute("aria-label", dark ? "Activer le thème clair" : "Activer le thème sombre");
  themeSwitchLabel.textContent = dark ? "Sombre" : "Clair";
}
applyTheme(document.documentElement.dataset.theme || "light");
themeSwitch.addEventListener("click", () => {
  const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("hauqe-theme", theme); applyTheme(theme); window.dispatchEvent(new CustomEvent("hauqe:theme-change", { detail: { theme } }));
});


let shellAvatarObjectUrl = null;

function clearShellAvatarObjectUrl() {
  if (shellAvatarObjectUrl) {
    URL.revokeObjectURL(shellAvatarObjectUrl);
    shellAvatarObjectUrl = null;
  }
}

function applyShellAvatar(url = null, initialsText = "U") {
  document
    .querySelectorAll("#userMenuToggle .avatar, #accountDropdown .avatar")
    .forEach((element) => {
      if (url) {
        element.textContent = "";
        element.classList.add("has-image");
        element.style.backgroundImage = `url("${url}")`;
      } else {
        element.classList.remove("has-image");
        element.style.backgroundImage = "";
        element.textContent = initialsText;
      }
    });
}

async function hydrateShellAvatar(profile) {
  const initialsText = initials(profile);

  clearShellAvatarObjectUrl();
  applyShellAvatar(null, initialsText);

  if (!profile?.avatar_document_id) return;

  try {
    const blob = await apiBlob(
      "/api/v1/me/avatar",
      { suppressGlobalAuth: true }
    );

    shellAvatarObjectUrl = URL.createObjectURL(blob);
    applyShellAvatar(shellAvatarObjectUrl, initialsText);
  } catch (error) {
    if (error?.status !== 404) {
      console.warn("Chargement avatar navbar :", error);
    }
  }
}

function initials(profile) {
  const first = String(profile?.prenoms || "").trim();
  const last = String(profile?.nom || "").trim();
  return (
    `${first.charAt(0)}${last.charAt(0)}`
      .trim()
      .toUpperCase()
    || "U"
  );
}

function fullName(profile) {
  return [profile?.prenoms, profile?.nom]
    .filter(Boolean)
    .join(" ")
    .trim()
    || profile?.email
    || "Utilisateur";
}

function profileRole(profile) {
  return (
    profile?.fonction
    || profile?.roles?.[0]
    || "Utilisateur HAUQE"
  );
}

function applyProfileToShell(profile) {
  if (!profile) return;

  const name = fullName(profile);
  const role = profileRole(profile);
  const initialsText = initials(profile);

  document
    .querySelectorAll("#userMenuToggle .avatar, #accountDropdown .avatar")
    .forEach((element) => {
      if (!element.classList.contains("has-image")) {
        element.textContent = initialsText;
      }
    });

  const toggleName = document.querySelector(
    "#userMenuToggle .user-copy strong"
  );
  const toggleRole = document.querySelector(
    "#userMenuToggle .user-copy small"
  );
  const dropdownName = document.querySelector(
    "#accountDropdown header div strong"
  );
  const dropdownEmail = document.querySelector(
    "#accountDropdown header div small"
  );
  const dropdownRole = document.querySelector(
    "#accountDropdown header div em"
  );

  if (toggleName) toggleName.textContent = name;
  if (toggleRole) toggleRole.textContent = role;
  if (dropdownName) dropdownName.textContent = name;
  if (dropdownEmail) dropdownEmail.textContent = profile.email || "";
  if (dropdownRole) dropdownRole.textContent = role;

  const lockTitle = document.querySelector("#sessionLockTitle");
  const lockAvatar = document.querySelector(
    "#sessionLock .session-lock-avatar"
  );

  if (lockTitle) {
    lockTitle.textContent = `Bienvenue, ${profile.prenoms || profile.nom || "Utilisateur"}`;
  }
  if (lockAvatar) {
    const lockIcon = lockAvatar.querySelector("span");
    lockAvatar.childNodes[0].textContent = initialsText;
    if (lockIcon) lockAvatar.appendChild(lockIcon);
  }
}

async function hydrateAuthenticatedShell() {
  if (!hasAccessToken()) return;

  try {
    const profile = await getCurrentProfile({ force: true });
    applyProfileToShell(profile);
    await hydrateShellAvatar(profile);
  } catch (error) {
    console.error("Chargement du profil shell :", error);
  }
}


function getCachedProfileForAvatarFallback() {
  try {
    return JSON.parse(
      sessionStorage.getItem("hauqe-current-profile-cache") || "null"
    );
  } catch {
    return null;
  }
}

function bindProfileShortcuts() {
  document
    .querySelectorAll("[data-profile-shortcut]")
    .forEach((link) => {
      link.addEventListener("click", () => {
        sessionStorage.setItem(
          "hauqe-profile-shortcut",
          link.dataset.profileShortcut
        );
      });
    });
}

function bindRealLogout() {
  const logoutLink = document.querySelector(
    "#accountDropdown footer a[href='#/connexion']"
  );

  logoutLink?.addEventListener("click", async (event) => {
    event.preventDefault();

    try {
      await logout();
    } finally {
      location.hash = "#/connexion";
    }
  });
}

const notifications = [
  { icon: "triangle-alert", tone: "critical", title: "Certification à renouveler", text: "AGROVITA — ISO 22000 expire dans 2 jours.", time: "Il y a 8 min", link: "#/echeances" },
  { icon: "clipboard-check", tone: "info", title: "Nouvelle fiche affectée", text: "COL-2026-081 attend votre validation.", time: "Il y a 32 min", link: "#/validations" },
  { icon: "undo-2", tone: "warning", title: "Correction reçue", text: "Kara Fruits SARL a soumis ses corrections.", time: "Il y a 1 h", link: "#/validations" },
  { icon: "file-check-2", tone: "success", title: "Rapport disponible", text: "Le rapport mensuel a été généré.", time: "Hier à 17:42", link: "#/rapports" },
];

document.querySelector("#quickNotifications").innerHTML = notifications.map((item) => `<a class="quick-notification ${item.tone} unread" href="${item.link}"><span><i data-lucide="${item.icon}"></i></span><div><strong>${item.title}</strong><p>${item.text}</p><small>${item.time}</small></div><i data-lucide="chevron-right"></i></a>`).join("");

function closeTopbarDropdowns() {
  notificationDropdown.hidden = true; accountDropdown.hidden = true;
  notificationToggle.setAttribute("aria-expanded", "false"); userMenuToggle.setAttribute("aria-expanded", "false");
}

notificationToggle.addEventListener("click", (event) => {
  event.stopPropagation(); const open = notificationDropdown.hidden;
  closeTopbarDropdowns(); notificationDropdown.hidden = !open; notificationToggle.setAttribute("aria-expanded", String(open));
});
userMenuToggle.addEventListener("click", (event) => {
  event.stopPropagation(); const open = accountDropdown.hidden;
  closeTopbarDropdowns(); accountDropdown.hidden = !open; userMenuToggle.setAttribute("aria-expanded", String(open));
});
document.querySelector("#markNotificationsRead").addEventListener("click", () => {
  document.querySelectorAll(".quick-notification").forEach((item) => item.classList.remove("unread"));
  document.querySelector("#notificationDot").hidden = true;
  notificationDropdown.querySelector("header small").textContent = "Aucune non lue";
});
document.addEventListener("click", (event) => { if (!event.target.closest(".topbar-dropdown-wrap")) closeTopbarDropdowns(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeTopbarDropdowns(); });
document.querySelectorAll(".topbar-dropdown a").forEach((link) => link.addEventListener("click", closeTopbarDropdowns));
if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });

bindProfileShortcuts();
bindRealLogout();

window.addEventListener("hauqe:profile-updated", async (event) => {
  applyProfileToShell(event.detail);
  await hydrateShellAvatar(event.detail);
});

window.addEventListener("hauqe:avatar-updated", (event) => {
  const url = event.detail?.url || null;
  const profile = getCachedProfileForAvatarFallback();
  applyShellAvatar(url, initials(profile));
});

window.addEventListener("hauqe:auth-state", (event) => {
  if (event.detail?.authenticated) {
    hydrateAuthenticatedShell();
  }
});

initRouter();
initSessionLock();
hydrateAuthenticatedShell();
