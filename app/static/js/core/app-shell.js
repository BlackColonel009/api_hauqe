import { initRouter } from "./router.js";
import { initSessionLock } from "./session-lock.js";

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
initRouter();
initSessionLock();
