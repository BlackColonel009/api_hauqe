(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  let tab = "personal";
  let profile = null;
  let notificationPreferences = null;
  let securityLock = null;
  let sessions = [];
  let mfaStatus = null;
  let mfaEnrollment = null;
  let avatarObjectUrl = null;
  let avatarBusy = false;

  function icons() {
    if (window.lucide) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.8 }
      });
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatDateTime(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";

    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: profile?.fuseau_horaire || "Africa/Lome",
    }).format(date);
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";

    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "long",
      timeZone: profile?.fuseau_horaire || "Africa/Lome",
    }).format(date);
  }

  function initialsOf(item) {
    const first = String(item?.prenoms || "").trim();
    const last = String(item?.nom || "").trim();

    return (
      `${first.charAt(0)}${last.charAt(0)}`
        .trim()
        .toUpperCase()
      || "U"
    );
  }

  function displayName(item) {
    return [
      item?.prenoms,
      item?.nom
    ].filter(Boolean).join(" ").trim() || item?.email || "Utilisateur";
  }

  function primaryRole(item) {
    const roles = Array.isArray(item?.roles) ? item.roles : [];
    if (item?.fonction) return item.fonction;
    return roles[0] || "Utilisateur HAUQE";
  }


function revokeAvatarObjectUrl() {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl);
    avatarObjectUrl = null;
  }
}

function setHeroAvatar(url = null) {
  const container = $("#profileAvatar");
  const initials = $("#profileInitials");
  if (!container || !initials) return;

  const oldImage = $("#profileAvatarImage");
  if (oldImage) oldImage.remove();

  if (!url) {
    initials.hidden = false;
    container.classList.remove("has-image");
    return;
  }

  initials.hidden = true;
  container.classList.add("has-image");

  const image = document.createElement("img");
  image.id = "profileAvatarImage";
  image.src = url;
  image.alt = `Photo de profil de ${displayName(profile)}`;
  container.prepend(image);
}

async function loadAvatar() {
  const api = await import("/static/js/core/api.js");

  revokeAvatarObjectUrl();
  setHeroAvatar(null);

  /*
   * Route propriétaire dédiée.
   * Si aucun avatar n'existe, le backend répond 404 et les initiales restent.
   */
  try {
    const blob = await api.apiBlob(
      "/api/v1/me/avatar",
      { suppressGlobalAuth: true }
    );

    avatarObjectUrl = URL.createObjectURL(blob);
    setHeroAvatar(avatarObjectUrl);

    window.dispatchEvent(new CustomEvent(
      "hauqe:avatar-updated",
      { detail: { url: avatarObjectUrl } }
    ));
  } catch (error) {
    if (error?.status !== 404) {
      console.warn("Avatar non chargé :", error);
    }
  }
}

function updateTopSaveButton() {
  const button = $("#saveProfile");
  if (!button) return;

  const hidden = tab === "sessions";
  button.hidden = hidden;
  if (hidden) return;

  const text = button.querySelector("span");
  if (text) {
    text.textContent =
      tab === "security"
        ? "Enregistrer la sécurité"
        : "Enregistrer les modifications";
  }
}

function passwordFieldsTouched() {
  return Boolean(
    ($("#currentPassword")?.value || "")
    || ($("#newPassword")?.value || "")
    || ($("#confirmPassword")?.value || "")
  );
}

function securityLockFieldsChanged() {
  if (!securityLock) return false;

  const enabled = Boolean($("#pinEnabled")?.checked);
  const timeout = Number($("#sessionTimeout")?.value || 15);
  const newCode = $("#sessionPin")?.value || "";
  const confirmCode = $("#sessionPinConfirm")?.value || "";
  const currentPassword = $("#lockCurrentPassword")?.value || "";

  return (
    enabled !== Boolean(securityLock.enabled)
    || timeout !== Number(securityLock.timeout_minutes || 15)
    || Boolean(newCode)
    || Boolean(confirmCode)
    || Boolean(currentPassword)
  );
}

  function toast(message, error = false) {
    const box = $("#profileToast");
    if (!box) return;

    box.querySelector("span").textContent = message;
    box.classList.toggle("error", error);
    box.hidden = false;

    clearTimeout(box._timer);
    box._timer = setTimeout(() => {
      box.hidden = true;
    }, 2600);

    icons();
  }

  function loadingPanel(message = "Chargement…") {
    return `
      <div class="profile-loading-state">
        <span class="profile-loading-dot"></span>
        ${escapeHtml(message)}
      </div>
    `;
  }

  function errorPanel(message) {
    return `
      <div class="profile-api-state error">
        <i data-lucide="triangle-alert"></i>
        <div>
          <strong>Impossible de charger cette section</strong>
          <small>${escapeHtml(message)}</small>
        </div>
      </div>
    `;
  }

  function updateHero() {
    if (!profile) return;

    $("#profileInitials").textContent = initialsOf(profile);
    $("#profileHeroName").textContent = displayName(profile);
    $("#profileHeroRole").textContent = primaryRole(profile);

    const statusText = String(profile.statut || "INCONNU").toUpperCase();
    $("#profileHeroStatus span").textContent =
      statusText === "ACTIF" ? "Compte actif" : `Compte ${statusText.toLowerCase()}`;

    $("#profileHeroStatus").classList.toggle(
      "is-inactive",
      statusText !== "ACTIF"
    );

    $("#profileLastLogin").textContent =
      formatDateTime(profile.derniere_connexion_at);

    $("#profileCreatedAt").textContent =
      formatDate(profile.created_at);

    const mfa = $("#profileMfaState");
    mfa.textContent = profile.mfa_active ? "Activée" : "Désactivée";
    mfa.classList.toggle("secure", Boolean(profile.mfa_active));

    icons();
  }

  function personalView() {
    if (!profile) return loadingPanel("Chargement du profil…");

    return `
      <header class="profile-section-head">
        <h2>Informations personnelles</h2>
        <p>
          Mettez à jour vos coordonnées.
          Les habilitations et données administratives restent gérées par HAUQE.
        </p>
      </header>

      <div class="profile-form" id="personalProfileForm">
        <label>
          Prénom(s)
          <input
            id="profilePrenoms"
            value="${escapeHtml(profile.prenoms || "")}"
            autocomplete="given-name"
          >
        </label>

        <label>
          Nom
          <input
            id="profileNom"
            value="${escapeHtml(profile.nom || "")}"
            autocomplete="family-name"
          >
        </label>

        <label class="full">
          Adresse électronique professionnelle
          <input
            type="email"
            value="${escapeHtml(profile.email || "")}"
            disabled
          >
        </label>

        <label>
          Téléphone
          <input
            id="profileTelephone"
            value="${escapeHtml(profile.telephone || "")}"
            autocomplete="tel"
          >
        </label>

        <label>
          Fonction
          <input
            value="${escapeHtml(profile.fonction || "")}"
            disabled
          >
        </label>

        <label>
          Région d’affectation
          <input
            value="${escapeHtml(profile.region_affectation_nom || "—")}"
            disabled
          >
        </label>

        <label>
          Langue
          <select id="profileLangue">
            <option value="fr" ${profile.langue === "fr" ? "selected" : ""}>
              Français
            </option>
            <option value="en" ${profile.langue === "en" ? "selected" : ""}>
              English
            </option>
          </select>
        </label>

        <label>
          Fuseau horaire
          <select id="profileTimezone">
            <option
              value="Africa/Lome"
              ${profile.fuseau_horaire === "Africa/Lome" ? "selected" : ""}
            >
              Africa/Lomé — UTC+0
            </option>
          </select>
        </label>

        <div class="profile-readonly-note full">
          <i data-lucide="shield-check"></i>
          <span>
            Email, fonction, région, statut, rôles et permissions ne sont
            pas modifiables depuis Mon compte.
          </span>
        </div>
      </div>
    `;
  }

  function securityView() {
    if (!securityLock || !mfaStatus) {
      return loadingPanel("Chargement de la sécurité…");
    }

    const lockConfigured = securityLock.code_configured;
    const lockEnabled = securityLock.enabled;

    const mfaPanel = mfaEnrollment
      ? `
        <div class="profile-inline-card mfa-enrollment-card">
          <div>
            <strong>Finaliser l’activation MFA</strong>
            <small>
              Ajoutez cette clé dans votre application d’authentification,
              puis saisissez le code à 6 chiffres.
            </small>
          </div>

          <div class="mfa-secret-box">
            <code>${escapeHtml(mfaEnrollment.secret || mfaEnrollment.manual_key || mfaEnrollment.totp_secret || "")}</code>
            <button type="button" id="copyMfaSecret">
              <i data-lucide="copy"></i>
              Copier
            </button>
          </div>

          <label class="profile-inline-field">
            Code à 6 chiffres
            <input
              id="mfaEnrollmentCode"
              inputmode="numeric"
              autocomplete="one-time-code"
              placeholder="000000"
              maxlength="20"
            >
          </label>

          <div class="profile-inline-actions">
            <button
              class="btn btn-primary app-btn"
              id="verifyMfaEnrollment"
              type="button"
            >
              <i data-lucide="shield-check"></i>
              Confirmer l’activation
            </button>
            <button
              class="btn app-btn"
              id="cancelMfaEnrollment"
              type="button"
            >
              Annuler
            </button>
          </div>
        </div>
      `
      : "";

    return `
      <header class="profile-section-head">
        <h2>Sécurité du compte</h2>
        <p>
          Mot de passe, authentification multifacteur et verrouillage de reprise.
        </p>
      </header>

      <section class="profile-security-block">
        <div class="profile-security-title">
          <div>
            <strong>Changer le mot de passe</strong>
            <small>
              Les autres sessions seront révoquées après modification.
            </small>
          </div>
          <i data-lucide="key-round"></i>
        </div>

        <div class="profile-form profile-form-compact" id="passwordChangeForm">
          <label class="full">
            Mot de passe actuel
            <input
              id="currentPassword"
              type="password"
              autocomplete="current-password"
            >
          </label>

          <label>
            Nouveau mot de passe
            <input
              id="newPassword"
              type="password"
              autocomplete="new-password"
            >
          </label>

          <label>
            Confirmer le mot de passe
            <input
              id="confirmPassword"
              type="password"
              autocomplete="new-password"
            >
          </label>
        </div>

        <div class="profile-section-actions">
          <button
            class="btn app-btn"
            id="changePasswordButton"
            type="button"
          >
            <i data-lucide="key-square"></i>
            Modifier le mot de passe
          </button>
        </div>
      </section>

      <div class="setting-row">
        <div>
          <strong>Double authentification (MFA)</strong>
          <small>
            Code temporaire demandé à chaque nouvelle connexion.
            ${mfaStatus.recovery_codes_remaining
              ? `${mfaStatus.recovery_codes_remaining} code(s) de récupération restant(s).`
              : ""}
          </small>
        </div>

        <button
          class="profile-setting-button ${mfaStatus.active ? "danger" : ""}"
          id="${mfaStatus.active ? "disableMfa" : "enableMfa"}"
          type="button"
        >
          ${mfaStatus.active ? "Désactiver" : "Activer"}
        </button>
      </div>

      ${mfaPanel}

      <section class="session-pin-panel">
        <div class="session-pin-heading">
          <span>
            <i data-lucide="lock-keyhole"></i>
          </span>

          <div>
            <h3>Verrouillage automatique de session</h3>
            <p>
              Après une période d’inactivité, l’application masque les
              données et exige votre code privé.
            </p>
          </div>

          <label class="pin-switch">
            <input
              id="pinEnabled"
              type="checkbox"
              ${lockEnabled ? "checked" : ""}
            >
            <span></span>
          </label>
        </div>

        <div class="session-pin-form">
          <label>
            Mot de passe actuel
            <input
              id="lockCurrentPassword"
              type="password"
              autocomplete="current-password"
              placeholder="Requis seulement pour changer le code"
            >
          </label>

          <label>
            Nouveau code privé
            <input
              id="sessionPin"
              type="password"
              minlength="5"
              placeholder="${
                lockConfigured
                  ? "Laisser vide pour conserver le code actuel"
                  : "Au moins 5 caractères"
              }"
              autocomplete="new-password"
            >
          </label>

          <label>
            Confirmer le code
            <input
              id="sessionPinConfirm"
              type="password"
              minlength="5"
              placeholder="Répétez le nouveau code"
              autocomplete="new-password"
            >
          </label>

          <label>
            Délai d’inactivité
            <select id="sessionTimeout">
              ${[5, 10, 15, 30].map((minutes) => `
                <option
                  value="${minutes}"
                  ${Number(securityLock.timeout_minutes) === minutes ? "selected" : ""}
                >
                  ${minutes} minutes${minutes === 15 ? " — recommandé" : ""}
                </option>
              `).join("")}
            </select>
          </label>
        </div>

        <div class="session-pin-note">
          <i data-lucide="shield-check"></i>
          <p>
            <strong>Protection complémentaire</strong>
            <small>
              Le code privé est haché côté serveur et n’est jamais
              enregistré dans le navigateur.
            </small>
          </p>
        </div>

        <div class="session-pin-actions">
          <span>
            ${
              lockConfigured
                ? "Un code privé est configuré."
                : "Aucun code privé configuré."
            }
          </span>

          <div>
            <button
              type="button"
              class="btn app-btn"
              id="testSessionLock"
              ${!lockEnabled || !lockConfigured ? "disabled" : ""}
            >
              <i data-lucide="scan-face"></i>
              Tester
            </button>

            <button
              type="button"
              class="btn btn-primary app-btn"
              id="saveSessionPin"
            >
              <i data-lucide="key-round"></i>
              Enregistrer
            </button>
          </div>
        </div>
      </section>
    `;
  }

  function notificationsView() {
    if (!notificationPreferences) {
      return loadingPanel("Chargement des préférences…");
    }

    const items = [
      [
        "alertes_critiques",
        "Alertes critiques",
        "Échéances sensibles, retards et alertes majeures",
      ],
      [
        "affectations",
        "Affectations",
        "Nouveau dossier ou nouvelle tâche qui vous est affectée",
      ],
      [
        "corrections",
        "Corrections",
        "Retour, correction demandée ou nouvelle soumission",
      ],
      [
        "rapports_planifies",
        "Rapports planifiés",
        "Rapport généré ou en échec",
      ],
      [
        "resume_hebdomadaire",
        "Résumé hebdomadaire",
        "Synthèse préparée chaque semaine",
      ],
    ];

    return `
      <header class="profile-section-head">
        <h2>Préférences de notification</h2>
        <p>
          Choisissez les événements fonctionnels qui doivent vous être signalés.
          Les notifications de sécurité restent obligatoires.
        </p>
      </header>

      <div id="notificationPreferencesForm">
        ${items.map(([key, label, description]) => `
          <div class="setting-row">
            <div>
              <strong>${escapeHtml(label)}</strong>
              <small>${escapeHtml(description)}</small>
            </div>
            <input
              type="checkbox"
              data-notification-pref="${key}"
              ${notificationPreferences[key] ? "checked" : ""}
            >
          </div>
        `).join("")}
      </div>
    `;
  }

  function sessionLabel(session) {
    const ua = String(session.user_agent || "");
    if (!ua) return "Appareil non identifié";

    if (/android/i.test(ua)) return "Mobile · Android";
    if (/iphone|ipad/i.test(ua)) return "Mobile · iOS";
    if (/windows/i.test(ua) && /chrome/i.test(ua)) {
      return "Chrome · Windows";
    }
    if (/windows/i.test(ua)) return "Windows";
    if (/macintosh|mac os/i.test(ua)) return "macOS";
    if (/linux/i.test(ua)) return "Linux";

    return ua.length > 68 ? `${ua.slice(0, 68)}…` : ua;
  }

  function sessionsView() {
    if (!sessions) return loadingPanel("Chargement des sessions…");

    if (!sessions.length) {
      return `
        <header class="profile-section-head">
          <h2>Sessions et connexions</h2>
          <p>Surveillez les appareils connectés à votre compte.</p>
        </header>

        <div class="profile-empty-state">
          <i data-lucide="monitor-off"></i>
          <strong>Aucune session à afficher</strong>
          <small>Votre session courante n’a pas été retrouvée.</small>
        </div>
      `;
    }

    return `
      <header class="profile-section-head">
        <div>
          <h2>Sessions et connexions</h2>
          <p>Surveillez les appareils connectés à votre compte.</p>
        </div>
        <button
          class="btn app-btn"
          id="revokeOtherSessions"
          type="button"
        >
          <i data-lucide="log-out"></i>
          Déconnecter les autres
        </button>
      </header>

      ${sessions.map((session) => `
        <div class="session-row ${session.current ? "current" : ""}">
          <div class="session-device-icon">
            <i data-lucide="${
              /mobile|android|iphone/i.test(session.user_agent || "")
                ? "smartphone"
                : "monitor"
            }"></i>
          </div>

          <div class="session-row-copy">
            <strong>
              ${escapeHtml(sessionLabel(session))}
              ${session.current ? '<span class="session-current-badge">Actuelle</span>' : ""}
            </strong>
            <small>
              IP : ${escapeHtml(session.adresse_ip || "—")}
              · Dernière activité : ${escapeHtml(formatDateTime(session.derniere_activite_at))}
            </small>
            <small>
              Expiration : ${escapeHtml(formatDateTime(session.expiration_at))}
              ${session.locked ? " · Session verrouillée" : ""}
            </small>
          </div>

          <button
            type="button"
            class="${session.current ? "current-session-button" : ""}"
            data-revoke-session="${escapeHtml(session.id)}"
            ${session.current ? "disabled" : ""}
          >
            ${session.current ? "Actuelle" : "Déconnecter"}
          </button>
        </div>
      `).join("")}
    `;
  }

  const views = {
    personal: personalView,
    security: securityView,
    notifications: notificationsView,
    sessions: sessionsView,
  };

  async function ensureTabData() {
    const api = await import("/static/js/core/api.js");

    if (tab === "security") {
      const [lock, mfa] = await Promise.all([
        api.apiGet("/api/v1/me/security-lock"),
        api.apiGet("/api/v1/me/mfa"),
      ]);

      securityLock = lock;
      mfaStatus = mfa;
    }

    if (tab === "notifications") {
      notificationPreferences = await api.apiGet(
        "/api/v1/me/notification-preferences"
      );
    }

    if (tab === "sessions") {
      sessions = await api.apiGet("/api/v1/me/sessions");
    }
  }

  function render() {
    const content = $("#profileContent");
    const view = views[tab];

    content.innerHTML = view ? view() : errorPanel("Section inconnue.");

    $$("[data-profile-tab]").forEach((button) => {
      button.classList.toggle(
        "active",
        button.dataset.profileTab === tab
      );
    });

    bindCurrentView();
    updateTopSaveButton();
    icons();
  }

  async function switchTab(nextTab) {
    tab = nextTab;
    $("#profileContent").innerHTML = loadingPanel("Chargement…");
    icons();

    try {
      await ensureTabData();
      render();
    } catch (error) {
      const api = await import("/static/js/core/api.js");
      const info = api.describeApiError(error);
      $("#profileContent").innerHTML = errorPanel(info.message);
      icons();
    }
  }

  async function savePersonalProfile() {
    const api = await import("/static/js/core/api.js");
    const auth = await import("/static/js/core/auth.js");

    const currentValues = {
      prenoms: $("#profilePrenoms")?.value.trim() || null,
      nom: $("#profileNom")?.value.trim() || null,
      telephone: $("#profileTelephone")?.value.trim() || null,
      langue: $("#profileLangue")?.value || "fr",
      fuseau_horaire: $("#profileTimezone")?.value || "Africa/Lome",
    };

    /*
     * PATCH réel : seuls les champs effectivement modifiés sont envoyés.
     * Exemple si seul le téléphone change :
     *   { "telephone": "93356041" }
     */
    const payload = Object.fromEntries(
      Object.entries(currentValues).filter(([key, value]) => {
        const previous = profile?.[key] ?? null;
        return value !== previous;
      })
    );

    if (!Object.keys(payload).length) {
      toast("Aucune modification à enregistrer");
      return;
    }

    const button = $("#saveProfile");
    button.disabled = true;

    try {
      profile = await api.apiPatch(
        "/api/v1/me/profile",
        payload
      );
      auth.clearProfileCache();
      updateHero();
      render();
      toast("Profil mis à jour");
      window.dispatchEvent(new CustomEvent(
        "hauqe:profile-updated",
        { detail: profile }
      ));
    } catch (error) {
      const info = api.describeApiError(error);
      toast(info.message, true);
    } finally {
      button.disabled = false;
    }
  }

  async function changePassword({ quiet = false } = {}) {
    const api = await import("/static/js/core/api.js");

    const current = $("#currentPassword")?.value || "";
    const next = $("#newPassword")?.value || "";
    const confirm = $("#confirmPassword")?.value || "";

    if (!current || !next || !confirm) {
      if (!quiet) {
        toast("Renseignez les trois champs du mot de passe", true);
      }
      return false;
    }

    if (next !== confirm) {
      if (!quiet) {
        toast("Les nouveaux mots de passe ne correspondent pas", true);
      }
      return false;
    }

    try {
      await api.apiPost("/api/v1/me/password/change", {
        current_password: current,
        new_password: next,
        confirm_password: confirm,
      });

      $("#currentPassword").value = "";
      $("#newPassword").value = "";
      $("#confirmPassword").value = "";

      if (!quiet) {
        toast("Mot de passe modifié");
      }
      return true;
    } catch (error) {
      toast(api.describeApiError(error).message, true);
      return false;
    }
  }

  async function saveNotificationPreferences() {
    const api = await import("/static/js/core/api.js");

    const payload = {};
    $$("[data-notification-pref]").forEach((input) => {
      payload[input.dataset.notificationPref] = input.checked;
    });

    try {
      notificationPreferences = await api.apiPatch(
        "/api/v1/me/notification-preferences",
        payload
      );
      toast("Préférences enregistrées");
      render();
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function saveSecurityLock({ quiet = false, rerender = true } = {}) {
    const api = await import("/static/js/core/api.js");

    const newCode = $("#sessionPin")?.value || "";
    const confirmCode = $("#sessionPinConfirm")?.value || "";
    const currentPassword = $("#lockCurrentPassword")?.value || "";
    const enabled = Boolean($("#pinEnabled")?.checked);
    const timeoutMinutes = Number($("#sessionTimeout")?.value || 15);

    if (newCode && newCode.length < 5) {
      toast("Le code privé doit contenir au moins 5 caractères", true);
      return false;
    }

    if (newCode !== confirmCode) {
      toast("Les deux codes privés ne correspondent pas", true);
      return false;
    }

    if (newCode && !currentPassword) {
      toast(
        "Le mot de passe actuel est requis pour changer le code privé",
        true
      );
      return false;
    }

    const payload = {
      enabled,
      timeout_minutes: timeoutMinutes,
    };

    if (newCode) {
      payload.current_password = currentPassword;
      payload.new_code = newCode;
      payload.confirm_code = confirmCode;
    }

    try {
      securityLock = await api.apiPatch(
        "/api/v1/me/security-lock",
        payload
      );

      window.dispatchEvent(new CustomEvent(
        "hauqe:session-lock-settings",
        { detail: securityLock }
      ));

      if (!quiet) {
        toast("Protection de session enregistrée");
      }

      if (rerender) {
        render();
      }

      return true;
    } catch (error) {
      toast(api.describeApiError(error).message, true);
      return false;
    }
  }


async function saveSecurityFromTop() {
  const button = $("#saveProfile");
  const wantsPasswordChange = passwordFieldsTouched();
  const wantsLockChange = securityLockFieldsChanged();

  if (!wantsPasswordChange && !wantsLockChange) {
    toast("Aucune modification de sécurité à enregistrer");
    return;
  }

  if (button) button.disabled = true;

  try {
    if (wantsPasswordChange) {
      const passwordOk = await changePassword({ quiet: true });
      if (!passwordOk) return;
    }

    if (wantsLockChange) {
      const lockOk = await saveSecurityLock({
        quiet: true,
        rerender: false,
      });
      if (!lockOk) return;
    }

    /*
     * Recharge l'état de sécurité après les deux opérations afin que
     * l'interface reflète exactement ce que le serveur a persisté.
     */
    await ensureTabData();
    render();
    toast("Modifications de sécurité enregistrées");
  } finally {
    if (button) button.disabled = false;
  }
}

async function uploadAvatar(file) {
  if (!file || avatarBusy) return;

  const allowedTypes = new Set([
    "image/png",
    "image/jpeg",
  ]);

  const maxBytes = 3 * 1024 * 1024;

  if (!allowedTypes.has(file.type)) {
    toast("Format accepté : PNG, JPG ou JPEG", true);
    return;
  }

  if (file.size > maxBytes) {
    toast("La photo ne doit pas dépasser 3 Mo", true);
    return;
  }

  const api = await import("/static/js/core/api.js");
  const auth = await import("/static/js/core/auth.js");

  const formData = new FormData();
  formData.append("file", file);

  avatarBusy = true;
  $("#profileAvatar")?.classList.add("is-uploading");

  try {
    await api.apiPost(
      "/api/v1/me/avatar",
      formData
    );

    profile = await api.apiGet("/api/v1/me/profile");
    auth.clearProfileCache();

    updateHero();
    await loadAvatar();

    window.dispatchEvent(new CustomEvent(
      "hauqe:profile-updated",
      { detail: profile }
    ));

    toast("Photo de profil mise à jour");
  } catch (error) {
    toast(api.describeApiError(error).message, true);
  } finally {
    avatarBusy = false;
    $("#profileAvatar")?.classList.remove("is-uploading");

    const input = $("#avatarFileInput");
    if (input) input.value = "";
  }
}

  async function testSessionLock() {
    const api = await import("/static/js/core/api.js");

    try {
      securityLock = await api.apiPost(
        "/api/v1/me/security-lock/lock",
        { reason: "MANUAL_TEST" }
      );

      window.dispatchEvent(new CustomEvent(
        "hauqe:session-locked",
        { detail: securityLock }
      ));
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function enableMfa() {
    const api = await import("/static/js/core/api.js");

    try {
      mfaEnrollment = await api.apiPost(
        "/api/v1/me/mfa/enable",
        {}
      );
      render();
      toast("Clé MFA générée");
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function verifyMfaEnrollment() {
    const api = await import("/static/js/core/api.js");
    const auth = await import("/static/js/core/auth.js");

    const code = $("#mfaEnrollmentCode")?.value.trim();
    if (!code) {
      toast("Saisissez le code MFA", true);
      return;
    }

    try {
      const result = await api.apiPost(
        "/api/v1/me/mfa/verify",
        { code }
      );

      mfaEnrollment = null;
      mfaStatus = await api.apiGet("/api/v1/me/mfa");
      profile = await api.apiGet("/api/v1/me/profile");
      auth.clearProfileCache();

      updateHero();
      render();

      const recoveryCodes = result?.recovery_codes || [];
      if (recoveryCodes.length) {
        const text = recoveryCodes.join("\n");
        try {
          await navigator.clipboard.writeText(text);
          toast(
            "MFA activé — codes de récupération copiés dans le presse-papiers"
          );
        } catch {
          window.prompt(
            "MFA activé. Conservez ces codes de récupération en lieu sûr :",
            text
          );
        }
      } else {
        toast("MFA activé");
      }
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function disableMfa() {
    const api = await import("/static/js/core/api.js");

    const currentPassword = window.prompt(
      "Saisissez votre mot de passe actuel :"
    );
    if (!currentPassword) return;

    const code = window.prompt(
      "Saisissez un code MFA ou un code de récupération :"
    );
    if (!code) return;

    try {
      await api.apiPost(
        "/api/v1/me/mfa/disable",
        {
          current_password: currentPassword,
          code_or_recovery: code,
        }
      );

      mfaStatus = await api.apiGet("/api/v1/me/mfa");
      profile = await api.apiGet("/api/v1/me/profile");
      updateHero();
      render();
      toast("MFA désactivé");
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function revokeSession(sessionId) {
    const api = await import("/static/js/core/api.js");

    try {
      await api.apiPost(
        `/api/v1/me/sessions/${encodeURIComponent(sessionId)}/revoke`,
        {}
      );
      sessions = await api.apiGet("/api/v1/me/sessions");
      render();
      toast("Session révoquée");
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  async function revokeOtherSessions() {
    const api = await import("/static/js/core/api.js");

    try {
      const result = await api.apiPost(
        "/api/v1/me/sessions/revoke-others",
        {}
      );
      sessions = await api.apiGet("/api/v1/me/sessions");
      render();
      toast(
        `${result?.revoked_count || 0} autre(s) session(s) déconnectée(s)`
      );
    } catch (error) {
      toast(api.describeApiError(error).message, true);
    }
  }

  function bindCurrentView() {
    if (tab === "security") {
      $("#changePasswordButton")?.addEventListener(
        "click",
        changePassword
      );

      $("#saveSessionPin")?.addEventListener(
        "click",
        saveSecurityLock
      );

      $("#testSessionLock")?.addEventListener(
        "click",
        testSessionLock
      );

      $("#enableMfa")?.addEventListener(
        "click",
        enableMfa
      );

      $("#disableMfa")?.addEventListener(
        "click",
        disableMfa
      );

      $("#verifyMfaEnrollment")?.addEventListener(
        "click",
        verifyMfaEnrollment
      );

      $("#cancelMfaEnrollment")?.addEventListener("click", () => {
        mfaEnrollment = null;
        render();
      });

      $("#copyMfaSecret")?.addEventListener("click", async () => {
        if (!mfaEnrollment?.secret) return;
        try {
          await navigator.clipboard.writeText(
            mfaEnrollment.secret
          );
          toast("Clé MFA copiée");
        } catch {
          toast("Impossible de copier automatiquement", true);
        }
      });
    }

    if (tab === "sessions") {
      $$("[data-revoke-session]").forEach((button) => {
        if (button.disabled) return;

        button.addEventListener("click", () => {
          revokeSession(button.dataset.revokeSession);
        });
      });

      $("#revokeOtherSessions")?.addEventListener(
        "click",
        revokeOtherSessions
      );
    }
  }

  async function saveCurrentTab() {
    if (tab === "personal") {
      await savePersonalProfile();
      return;
    }

    if (tab === "notifications") {
      await saveNotificationPreferences();
      return;
    }

    if (tab === "security") {
      await saveSecurityFromTop();
      return;
    }

    toast("Aucune modification à enregistrer dans cette section");
  }

  async function logout() {
    const auth = await import("/static/js/core/auth.js");
    try {
      await auth.logout();
    } finally {
      location.hash = "#/connexion";
    }
  }

  function applyRequestedShortcut() {
    try {
      const shortcut = sessionStorage.getItem(
        "hauqe-profile-shortcut"
      );
      if (
        shortcut
        && ["personal", "security", "notifications", "sessions"]
          .includes(shortcut)
      ) {
        tab = shortcut;
      }
      sessionStorage.removeItem("hauqe-profile-shortcut");
    } catch {}
  }

  async function init() {
    const api = await import("/static/js/core/api.js");
    const auth = await import("/static/js/core/auth.js");

    applyRequestedShortcut();

    try {
      profile = await api.apiGet("/api/v1/me/profile");
      auth.clearProfileCache();
      updateHero();
      await loadAvatar();

      await ensureTabData();
      render();
    } catch (error) {
      const info = api.describeApiError(error);
      $("#profileContent").innerHTML = errorPanel(info.message);
      toast(info.message, true);
      icons();
      return;
    }

    $$("[data-profile-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        switchTab(button.dataset.profileTab);
      });
    });

    $("#saveProfile")?.addEventListener(
      "click",
      saveCurrentTab
    );

    updateTopSaveButton();

    $("#changeAvatar")?.addEventListener("click", () => {
      $("#avatarFileInput")?.click();
    });

    $("#avatarFileInput")?.addEventListener("change", async (event) => {
      const file = event.target.files?.[0] || null;
      if (file) {
        await uploadAvatar(file);
      }
    });

    $("#profileLogout")?.addEventListener(
      "click",
      async (event) => {
        event.preventDefault();
        await logout();
      }
    );

    icons();
  }


window.addEventListener("hashchange", () => {
  if (!location.hash.startsWith("#/profil")) {
    revokeAvatarObjectUrl();
  }
});

  init();
})();
