import { installActionLoader } from "./action-loader.js";
import { initRouter } from "./router.js";
import { initSessionLock } from "./session-lock.js";
import {
  getCurrentProfile,
  logout,
} from "./auth.js";
import {
  ApiError,
  apiBlob,
  apiGet,
  apiPost,
  hasAccessToken,
} from "./api.js";

installActionLoader();

document.querySelector("#menuToggle").addEventListener("click", () => document.querySelector("#sidebar").classList.toggle("open"));
document.addEventListener("click", (event) => {
  const disabledLink = event.target.closest(".nav-link.disabled");
  if (disabledLink) event.preventDefault();
});

const notificationToggle = document.querySelector("#notificationToggle");
const notificationDropdown = document.querySelector("#notificationDropdown");
const userMenuToggle = document.querySelector("#userMenuToggle");
const accountDropdown = document.querySelector("#accountDropdown");
const presenceWrap = document.querySelector("#presenceWrap");
const presenceToggle = document.querySelector("#presenceToggle");
const presenceDropdown = document.querySelector("#presenceDropdown");
const presenceCount = document.querySelector("#presenceCount");
const presenceSummary = document.querySelector("#presenceSummary");
const presenceState = document.querySelector("#presenceState");
const presenceUsers = document.querySelector("#presenceUsers");
const presenceRefresh = document.querySelector("#presenceRefresh");
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

/* ============================================================
   PRÉSENCE UTILISATEURS
   ------------------------------------------------------------
   - GET /api/v1/presence/users?minutes=15&limit=6
   - POST /api/v1/presence/heartbeat
   - avatars chargés en Blob avec Bearer token
   - le heartbeat est déclenché uniquement par une vraie activité
     utilisateur, jamais par le polling.
   ============================================================ */

const PRESENCE_WINDOW_MINUTES = 15;
const PRESENCE_LIST_LIMIT = 6;
const PRESENCE_REFRESH_MS = 60_000;
const PRESENCE_HEARTBEAT_THROTTLE_MS = 60_000;

let presenceRefreshTimer = null;
let lastPresenceFetchAt = 0;
let lastHeartbeatAt = 0;
let presenceForbidden = false;
let presenceAvatarObjectUrls = [];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function clearPresenceAvatarUrls() {
  presenceAvatarObjectUrls.forEach((url) => {
    try { URL.revokeObjectURL(url); } catch {}
  });
  presenceAvatarObjectUrls = [];
}

function presenceInitials(item) {
  const parts = String(item?.nom_complet || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (!parts.length) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0] || ""}${parts.at(-1)?.[0] || ""}`
    .toUpperCase();
}

function presenceRole(item) {
  const roles = Array.isArray(item?.roles) ? item.roles : [];
  const first = roles[0];

  return (
    first?.libelle
    || first?.code?.replaceAll("_", " ")
    || item?.fonction
    || "Utilisateur HAUQE"
  );
}

function presenceTimeLabel(item) {
  if (item?.presence === "ONLINE") {
    return "Actif maintenant";
  }

  const value = item?.last_activity_at;
  if (!value) return "Activité récente";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Activité récente";

  const minutes = Math.max(
    1,
    Math.floor((Date.now() - date.getTime()) / 60_000)
  );

  return `Actif il y a ${minutes} min`;
}

function renderPresenceState(message, {
  error = false,
  loading = false,
} = {}) {
  if (!presenceState) return;

  presenceState.hidden = false;
  presenceState.classList.toggle("is-error", error);
  presenceState.classList.toggle("is-loading", loading);
  presenceState.innerHTML = `
    <i data-lucide="${error ? "triangle-alert" : loading ? "loader-circle" : "users-round"}"></i>
    <span>${escapeHtml(message)}</span>
  `;

  if (window.lucide) {
    window.lucide.createIcons({
      attrs: { "stroke-width": 1.8 },
    });
  }
}

async function hydratePresenceAvatars(items) {
  clearPresenceAvatarUrls();

  const avatarItems = (items || []).filter(
    (item) => item?.has_avatar && item?.avatar_url
  );

  await Promise.allSettled(
    avatarItems.map(async (item) => {
      try {
        const blob = await apiBlob(
          item.avatar_url,
          { suppressGlobalAuth: true }
        );

        const url = URL.createObjectURL(blob);
        presenceAvatarObjectUrls.push(url);

        const target = presenceUsers?.querySelector(
          `.presence-avatar[data-user-id="${CSS.escape(String(item.user_id))}"]`
        );

        if (target) {
          target.classList.add("has-image");
          target.style.backgroundImage = `url("${url}")`;

          const initialsNode = target.querySelector(
            ".presence-avatar-initials"
          );
          if (initialsNode) initialsNode.textContent = "";
        }
      } catch {
        // Les initiales restent le fallback normal.
      }
    })
  );
}

function renderPresence(payload) {
  const items = Array.isArray(payload?.users)
    ? payload.users
    : [];

  if (presenceWrap) {
    presenceWrap.hidden = false;
  }

  if (presenceCount) {
    presenceCount.textContent = String(
      payload?.total_count ?? items.length
    );
  }

  if (presenceSummary) {
    const online = Number(payload?.online_count || 0);
    const recent = Number(payload?.recent_count || 0);

    presenceSummary.textContent =
      `${online} en ligne · ${recent} récent${recent > 1 ? "s" : ""} · ${PRESENCE_WINDOW_MINUTES} min`;
  }

  if (!presenceUsers) return;

  if (!items.length) {
    presenceUsers.innerHTML = "";
    renderPresenceState(
      "Aucun utilisateur actif dans les 15 dernières minutes."
    );
    return;
  }

  if (presenceState) {
    presenceState.hidden = true;
  }

  presenceUsers.innerHTML = items.map((item) => {
    const online = item.presence === "ONLINE";
    const initialsText = presenceInitials(item);

    return `
      <a
        class="presence-user"
        href="#/utilisateurs"
        data-presence-user="${escapeHtml(item.user_id)}"
      >
        <span
          class="presence-avatar"
          data-user-id="${escapeHtml(item.user_id)}"
        >
          <span class="presence-avatar-initials">${escapeHtml(initialsText)}</span>
          <b class="presence-dot ${online ? "online" : "recent"}" aria-hidden="true"></b>
        </span>

        <span class="presence-user-copy">
          <strong>${escapeHtml(item.nom_complet || "Utilisateur")}</strong>
          <em>${escapeHtml(presenceRole(item))}</em>
          <small>${escapeHtml(presenceTimeLabel(item))}</small>
        </span>

        ${item.is_current_user ? '<em class="presence-you">Vous</em>' : ""}
      </a>
    `;
  }).join("");

  hydratePresenceAvatars(items);
}

async function refreshPresence({
  force = false,
  silent = false,
} = {}) {
  if (
    !hasAccessToken()
    || presenceForbidden
    || !presenceWrap
  ) {
    return;
  }

  const now = Date.now();

  if (!force && now - lastPresenceFetchAt < 10_000) {
    return;
  }

  lastPresenceFetchAt = now;

  if (!silent) {
    renderPresenceState(
      "Actualisation de la présence…",
      { loading: true }
    );
  }

  presenceRefresh?.classList.add("is-loading");

  try {
    const payload = await apiGet(
      `/api/v1/presence/users?minutes=${PRESENCE_WINDOW_MINUTES}&limit=${PRESENCE_LIST_LIMIT}`,
      { suppressGlobalAuth: true }
    );

    renderPresence(payload);
  } catch (error) {
    if (error instanceof ApiError && error.status === 403) {
      presenceForbidden = true;
      presenceWrap.hidden = true;
      return;
    }

    if (!silent) {
      renderPresenceState(
        "Impossible de charger les utilisateurs actifs.",
        { error: true }
      );
    }
  } finally {
    presenceRefresh?.classList.remove("is-loading");
  }
}

async function sendPresenceHeartbeat({
  force = false,
} = {}) {
  if (
    !hasAccessToken()
    || document.hidden
    || document.body.classList.contains("session-is-locked")
  ) {
    return;
  }

  const now = Date.now();

  if (
    !force
    && now - lastHeartbeatAt < PRESENCE_HEARTBEAT_THROTTLE_MS
  ) {
    return;
  }

  lastHeartbeatAt = now;

  try {
    await apiPost(
      "/api/v1/presence/heartbeat",
      null,
      { suppressGlobalAuth: true }
    );
  } catch {
    // Le heartbeat ne doit jamais perturber une action métier.
  }
}

function startPresenceRuntime() {
  if (!hasAccessToken() || presenceForbidden) return;

  if (presenceWrap) {
    presenceWrap.hidden = false;
  }

  sendPresenceHeartbeat({ force: true });
  refreshPresence({ force: true, silent: true });

  if (!presenceRefreshTimer) {
    presenceRefreshTimer = window.setInterval(() => {
      if (!document.hidden && hasAccessToken()) {
        refreshPresence({ silent: true });
      }
    }, PRESENCE_REFRESH_MS);
  }
}

function stopPresenceRuntime() {
  if (presenceRefreshTimer) {
    clearInterval(presenceRefreshTimer);
    presenceRefreshTimer = null;
  }

  clearPresenceAvatarUrls();

  if (presenceWrap) {
    presenceWrap.hidden = true;
  }

  if (presenceDropdown) {
    presenceDropdown.hidden = true;
  }

  presenceToggle?.setAttribute("aria-expanded", "false");
}

[
  "pointerdown",
  "keydown",
  "touchstart",
  "wheel",
].forEach((eventName) => {
  window.addEventListener(
    eventName,
    () => sendPresenceHeartbeat(),
    { passive: true }
  );
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && hasAccessToken()) {
    sendPresenceHeartbeat({ force: true });
    refreshPresence({ force: true, silent: true });
  }
});

presenceRefresh?.addEventListener("click", async (event) => {
  event.stopPropagation();
  await refreshPresence({ force: true });
});

/* ============================================================
   NOTIFICATIONS RÉELLES
   ============================================================ */

let notificationForbidden = false;
let notificationRefreshTimer = null;
const NOTIFICATION_REFRESH_MS = 60_000;

function notificationTime(value) {
  if (!value) return "Notification récente";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Notification récente";

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function renderNotificationState(message, icon = "bell-off") {
  const container = document.querySelector("#quickNotifications");
  if (!container) return;

  container.innerHTML = `
    <div class="quick-notification-state">
      <i data-lucide="${icon}"></i>
      <span>${escapeHtml(message)}</span>
    </div>
  `;

  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  }
}

function notificationTone(item) {
  const text = `${item?.objet || ""} ${item?.contenu || ""}`.toUpperCase();

  if (text.includes("CRITIQUE") || text.includes("EXPIR")) return "critical";
  if (text.includes("URGENT") || text.includes("RETARD")) return "warning";
  if ((item?.statut || "").toUpperCase() === "ENVOYEE") return "success";
  return "info";
}

function notificationIcon(item) {
  const tone = notificationTone(item);
  if (tone === "critical") return "triangle-alert";
  if (tone === "warning") return "clock-alert";
  if (tone === "success") return "circle-check-big";
  return "bell-ring";
}

async function refreshNotifications({ silent = false } = {}) {
  if (!hasAccessToken() || notificationForbidden) return;

  if (!silent) {
    renderNotificationState(
      "Chargement des notifications…",
      "loader-circle"
    );
  }

  try {
    const payload = await apiGet(
      "/api/v1/notifications?limit=6&offset=0"
    );

    const container = document.querySelector("#quickNotifications");
    const headerSmall = notificationDropdown?.querySelector("header small");
    const dot = document.querySelector("#notificationDot");
    const items = Array.isArray(payload?.items) ? payload.items : [];
    const unread = Number(payload?.unread_count || 0);

    if (headerSmall) {
      headerSmall.textContent = unread
        ? `${unread} non lue${unread > 1 ? "s" : ""}`
        : "Aucune non lue";
    }

    if (dot) dot.hidden = unread === 0;

    if (!items.length) {
      renderNotificationState("Aucune notification.");
      return;
    }

    container.innerHTML = items.map((item) => `
      <button
        class="quick-notification ${notificationTone(item)} ${item.date_lecture ? "" : "unread"}"
        type="button"
        data-notification-id="${escapeHtml(item.id)}"
      >
        <span>
          <i data-lucide="${notificationIcon(item)}"></i>
        </span>

        <div>
          <strong>${escapeHtml(item.objet || "Notification")}</strong>
          <p>${escapeHtml(item.contenu || "")}</p>
          <small>
            ${escapeHtml(notificationTime(item.created_at || item.date_envoi))}
          </small>
        </div>

        <i data-lucide="chevron-right"></i>
      </button>
    `).join("");

    container
      .querySelectorAll("[data-notification-id]")
      .forEach((button) => {
        button.addEventListener("click", async () => {
          const item = items.find(
            (candidate) => String(candidate.id)
              === String(button.dataset.notificationId)
          );

          try {
            if (item && !item.date_lecture) {
              await apiPost(
                `/api/v1/notifications/${item.id}/read`,
                {}
              );
            }
          } catch (error) {
            console.warn("Lecture notification :", error);
          }

          closeTopbarDropdowns();
          location.hash = "#/alertes";
          await refreshNotifications({ silent: true });
        });
      });

    if (window.lucide) {
      window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
    }
  } catch (error) {
    if (error?.status === 403) {
      notificationForbidden = true;
      const dot = document.querySelector("#notificationDot");
      if (dot) dot.hidden = true;
      renderNotificationState(
        "Notifications non disponibles pour ce rôle."
      );
      return;
    }

    if (!silent) {
      renderNotificationState(
        error?.message || "Impossible de charger les notifications."
      );
    }
  }
}

function startNotificationRuntime() {
  if (!hasAccessToken() || notificationForbidden) return;

  refreshNotifications({ silent: true });

  if (notificationRefreshTimer) {
    clearInterval(notificationRefreshTimer);
  }

  notificationRefreshTimer = setInterval(
    () => refreshNotifications({ silent: true }),
    NOTIFICATION_REFRESH_MS
  );
}

function stopNotificationRuntime() {
  if (notificationRefreshTimer) {
    clearInterval(notificationRefreshTimer);
    notificationRefreshTimer = null;
  }
}

function closeTopbarDropdowns() {
  notificationDropdown.hidden = true;
  accountDropdown.hidden = true;

  if (presenceDropdown) {
    presenceDropdown.hidden = true;
  }

  notificationToggle.setAttribute("aria-expanded", "false");
  userMenuToggle.setAttribute("aria-expanded", "false");
  presenceToggle?.setAttribute("aria-expanded", "false");
}

presenceToggle?.addEventListener("click", async (event) => {
  event.stopPropagation();

  const open = presenceDropdown?.hidden ?? true;

  closeTopbarDropdowns();

  if (open && presenceDropdown) {
    presenceDropdown.hidden = false;
    presenceToggle.setAttribute("aria-expanded", "true");
    await refreshPresence({ force: true });
  }
});

notificationToggle.addEventListener("click", async (event) => {
  event.stopPropagation();

  const open = notificationDropdown.hidden;

  closeTopbarDropdowns();
  notificationDropdown.hidden = !open;
  notificationToggle.setAttribute("aria-expanded", String(open));

  if (open) {
    await refreshNotifications();
  }
});
userMenuToggle.addEventListener("click", (event) => {
  event.stopPropagation(); const open = accountDropdown.hidden;
  closeTopbarDropdowns(); accountDropdown.hidden = !open; userMenuToggle.setAttribute("aria-expanded", String(open));
});
document.querySelector("#markNotificationsRead").addEventListener(
  "click",
  async (event) => {
    event.stopPropagation();

    try {
      await apiPost("/api/v1/notifications/read-all", {});
      await refreshNotifications({ silent: true });
    } catch (error) {
      console.warn("Lecture globale notifications :", error);
    }
  }
);
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
    presenceForbidden = false;
    hydrateAuthenticatedShell();
    startPresenceRuntime();
    startNotificationRuntime();
  } else {
    stopPresenceRuntime();
    stopNotificationRuntime();
  }
});

initRouter();
initSessionLock();
hydrateAuthenticatedShell();

if (hasAccessToken()) {
  startPresenceRuntime();
  startNotificationRuntime();
} else {
  stopPresenceRuntime();
  stopNotificationRuntime();
}
