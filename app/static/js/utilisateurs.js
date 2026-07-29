(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  let currentUser = null;
  let users = [];
  let roles = [];
  let selectedUser = null;
  let editingUser = null;
  let searchTimer = null;

  const filters = {
    search: "",
    role: "",
    status: "",
    sort: "name",
  };

  function e(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function icons() {
    window.lucide?.createIcons({
      attrs: { "stroke-width": 1.8 },
    });
  }

  function hasPermission(code) {
    return Array.isArray(currentUser?.permissions)
      && currentUser.permissions.includes(code);
  }

  function state(message, error = false) {
    const node = $("#usersApiState");
    node.hidden = false;
    node.className =
      `dashboard-api-state ${error ? "error" : ""}`.trim();

    node.innerHTML = `
      <i data-lucide="${error ? "triangle-alert" : "info"}"></i>
      <div>
        <strong>${error ? "Opération impossible" : "Information"}</strong>
        <span>${e(message)}</span>
      </div>
    `;

    icons();
  }

  function hideState() {
    $("#usersApiState").hidden = true;
  }

  async function run(task, options = {}) {
    if (window.HAUQE_ACTION_LOADER) {
      return window.HAUQE_ACTION_LOADER.run(task, options);
    }

    return task();
  }

  function initials(user) {
    const first = String(user?.prenoms || "").trim();
    const last = String(user?.nom || "").trim();

    const value = `${first.charAt(0)}${last.charAt(0)}`.trim();

    if (value) return value.toUpperCase();

    return String(user?.email || "--")
      .slice(0, 2)
      .toUpperCase();
  }

  function displayName(user) {
    const value = [
      user?.prenoms,
      user?.nom,
    ].filter(Boolean).join(" ").trim();

    return value || user?.email || "Utilisateur";
  }

  function formatDateTime(value) {
    if (!value) return "Jamais";

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);

    return new Intl.DateTimeFormat("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  function roleByCode(code) {
    return roles.find(
      (role) => String(role.code) === String(code)
    ) || null;
  }

  function roleClass(code) {
    if (code === "ADMIN_HAUQE") return "admin";
    if (code === "DIRECTION_TECHNIQUE") return "direction";
    if (code === "AGENT_COLLECTE") return "collecte";
    if (code === "VERIFICATEUR") return "verification";
    if (code === "CONTROLEUR_FUCCS") return "fuccs";
    if (code === "CELLULE_VEILLE") return "veille";
    return "";
  }

  function roleLabel(code) {
    return roleByCode(code)?.libelle || code;
  }

  async function loadData() {
    const [me, userRows, roleRows] = await Promise.all([
      api.apiGet("/api/v1/me"),
      api.apiGet("/api/v1/users"),
      api.apiGet("/api/v1/roles"),
    ]);

    currentUser = me;
    users = Array.isArray(userRows) ? userRows : [];
    roles = (Array.isArray(roleRows) ? roleRows : [])
      .filter((role) =>
        String(role.statut || "").toUpperCase() === "ACTIF"
      )
      .sort((a, b) =>
        Number(b.niveau || 0) - Number(a.niveau || 0)
      );

    if (
      selectedUser
      && !users.some(
        (item) => String(item.id) === String(selectedUser.id)
      )
    ) {
      selectedUser = null;
      closeDrawer();
    }

    populateFilters();
    renderRoleCatalog();
    renderKpis();
    renderUsers();

    if (selectedUser) {
      selectedUser = users.find(
        (item) => String(item.id) === String(selectedUser.id)
      ) || null;

      if (selectedUser) renderDrawer();
    }
  }

  function populateFilters() {
    const select = $("#userRoleFilter");
    const current = select.value;

    select.innerHTML = `
      <option value="">Tous les rôles</option>
      ${roles.map((role) => `
        <option value="${e(role.code)}">
          ${e(role.libelle)} · ${e(role.code)}
        </option>
      `).join("")}
    `;

    select.value = current;
  }

  function renderRoleCatalog() {
    $("#roleCatalogCount").textContent =
      `${roles.length} rôle${roles.length > 1 ? "s" : ""}`;

    $("#roleCatalogList").innerHTML = roles.length
      ? roles.map((role) => `
          <article class="role-catalog-card ${roleClass(role.code)}">
            <span><i data-lucide="${role.code === "AGENT_COLLECTE" ? "clipboard-pen-line" : "badge-check"}"></i></span>
            <div>
              <strong>${e(role.libelle)}</strong>
              <code>${e(role.code)}</code>
              <small>${e(role.description || "Aucune description.")}</small>
            </div>
            <b>N${e(role.niveau ?? "—")}</b>
          </article>
        `).join("")
      : `
        <div class="priority-empty compact">
          Aucun rôle actif disponible.
        </div>
      `;

    icons();
  }

  function renderKpis() {
    const total = users.length;
    const active = users.filter(
      (user) => String(user.statut).toUpperCase() === "ACTIF"
    ).length;
    const inactive = users.filter(
      (user) => String(user.statut).toUpperCase() === "INACTIF"
    ).length;
    const mfa = users.filter(
      (user) => Boolean(user.mfa_active)
    ).length;
    const withoutRole = users.filter(
      (user) => !Array.isArray(user.roles) || !user.roles.length
    ).length;

    const cards = [
      ["users-round", "Utilisateurs", total, "Comptes en base", "green"],
      ["user-check", "Actifs", active, "Accès autorisé", "blue"],
      ["user-x", "Inactifs", inactive, "Sessions révoquées", "orange"],
      ["shield-check", "MFA activée", mfa, "Comptes renforcés", "gray"],
      ["badge-alert", "Sans rôle", withoutRole, "À habiliter", "red"],
    ];

    $("#userKpis").innerHTML = cards.map(
      ([icon, label, value, detail, tone]) => `
        <article class="user-kpi ${tone}">
          <span><i data-lucide="${icon}"></i></span>
          <div>
            <small>${e(label)}</small>
            <strong>${e(value)}</strong>
            <em>${e(detail)}</em>
          </div>
        </article>
      `
    ).join("");

    icons();
  }

  function filteredUsers() {
    const search = filters.search.toLowerCase();

    const rows = users.filter((user) => {
      if (
        filters.status
        && String(user.statut || "").toUpperCase()
          !== filters.status
      ) {
        return false;
      }

      if (
        filters.role
        && !Array.isArray(user.roles)
      ) {
        return false;
      }

      if (
        filters.role
        && !user.roles.includes(filters.role)
      ) {
        return false;
      }

      if (!search) return true;

      return [
        displayName(user),
        user.email,
        user.fonction,
        ...(user.roles || []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(search);
    });

    rows.sort((a, b) => {
      if (filters.sort === "recent") {
        return new Date(b.derniere_connexion_at || 0)
          - new Date(a.derniere_connexion_at || 0);
      }

      if (filters.sort === "role") {
        return String(a.roles?.[0] || "")
          .localeCompare(String(b.roles?.[0] || ""));
      }

      return displayName(a).localeCompare(
        displayName(b),
        "fr",
        { sensitivity: "base" }
      );
    });

    return rows;
  }

  function renderUsers() {
    const visible = filteredUsers();

    $("#userCount").textContent =
      `${visible.length} utilisateur${visible.length > 1 ? "s" : ""}`;

    $("#userResults").innerHTML = visible.length
      ? `
        <div class="table-responsive">
          <table class="table user-table real-user-table">
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Fonction</th>
                <th>Rôle(s)</th>
                <th>Dernière connexion</th>
                <th>Statut</th>
                <th>MFA</th>
                <th></th>
              </tr>
            </thead>

            <tbody>
              ${visible.map((user) => `
                <tr data-user-id="${e(user.id)}">
                  <td>
                    <div class="user-identity">
                      <span class="user-avatar">${e(initials(user))}</span>
                      <div>
                        <strong>${e(displayName(user))}</strong>
                        <small>${e(user.email)}</small>
                      </div>
                    </div>
                  </td>

                  <td>${e(user.fonction || "—")}</td>

                  <td>
                    <div class="table-role-list">
                      ${
                        user.roles?.length
                          ? user.roles.map((code) => `
                              <span class="role-badge ${roleClass(code)}">
                                ${e(roleLabel(code))}
                              </span>
                            `).join("")
                          : `<span class="role-badge empty">Aucun rôle</span>`
                      }
                    </div>
                  </td>

                  <td>${e(formatDateTime(user.derniere_connexion_at))}</td>

                  <td>
                    <span class="user-status ${String(user.statut || "").toLowerCase()}">
                      <i></i>
                      ${e(user.statut || "—")}
                    </span>
                  </td>

                  <td>
                    <span class="mfa-state ${user.mfa_active ? "on" : "off"}">
                      <i data-lucide="${user.mfa_active ? "shield-check" : "shield-off"}"></i>
                      ${user.mfa_active ? "Activée" : "Non"}
                    </span>
                  </td>

                  <td>
                    <button class="user-action" type="button">
                      <i data-lucide="chevron-right"></i>
                    </button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `
      : `
        <div class="user-empty">
          <i data-lucide="users-round"></i>
          <strong>Aucun utilisateur trouvé</strong>
          <span>Modifiez les filtres ou créez un nouveau compte.</span>
        </div>
      `;

    $$("[data-user-id]").forEach((row) => {
      row.onclick = () => {
        selectedUser = users.find(
          (item) => String(item.id) === String(row.dataset.userId)
        ) || null;

        if (selectedUser) openDrawer();
      };
    });

    icons();
  }

  function renderDrawer() {
    if (!selectedUser) return;

    $("#drawerAvatar").textContent = initials(selectedUser);
    $("#drawerName").textContent = displayName(selectedUser);
    $("#drawerEmail").textContent = selectedUser.email;

    $("#userProfileCard").innerHTML = `
      <h3>Informations du compte</h3>

      ${[
        ["Fonction", selectedUser.fonction || "—"],
        ["Téléphone", selectedUser.telephone || "—"],
        ["Statut", selectedUser.statut || "—"],
        ["MFA", selectedUser.mfa_active ? "Activée" : "Non activée"],
        [
          "Dernière connexion",
          formatDateTime(selectedUser.derniere_connexion_at),
        ],
      ].map(([label, value]) => `
        <div class="profile-row">
          <span>${e(label)}</span>
          <strong>${e(value)}</strong>
        </div>
      `).join("")}
    `;

    $("#selectedUserRoleCount").textContent =
      `${selectedUser.roles?.length || 0} actif(s)`;

    const canManageRoles = hasPermission(
      "UTILISATEURS.GERER_ROLES"
    );

    $("#drawerRoleList").innerHTML = roles.map((role) => {
      const checked = selectedUser.roles?.includes(role.code);
      const protectedOwnAdmin = (
        String(selectedUser.id) === String(currentUser.id)
        && role.code === "ADMIN_HAUQE"
        && checked
      );

      return `
        <label class="drawer-role-option ${checked ? "selected" : ""}">
          <input
            type="checkbox"
            value="${e(role.id)}"
            data-role-code="${e(role.code)}"
            ${checked ? "checked" : ""}
            ${(!canManageRoles || protectedOwnAdmin) ? "disabled" : ""}
          >

          <span>
            <strong>${e(role.libelle)}</strong>
            <code>${e(role.code)}</code>
            <small>${e(role.description || "—")}</small>
          </span>

          ${
            protectedOwnAdmin
              ? `<em>Protégé</em>`
              : ""
          }
        </label>
      `;
    }).join("");

    $("#saveUserRoles").hidden = !canManageRoles;
    $("#editUser").hidden = !hasPermission("UTILISATEURS.MODIFIER");
    $("#changeUserStatus").hidden =
      !hasPermission("UTILISATEURS.DESACTIVER");

    $("#userOverlay").hidden = false;
    $("#userDrawer").classList.add("open");
    $("#userDrawer").setAttribute("aria-hidden", "false");

    icons();
  }

  function openDrawer() {
    renderDrawer();
  }

  function closeDrawer() {
    $("#userOverlay").hidden = true;
    $("#userDrawer").classList.remove("open");
    $("#userDrawer").setAttribute("aria-hidden", "true");
  }

  function renderModalRoles(selectedCodes = []) {
    $("#modalRoleList").innerHTML = roles.map((role) => `
      <label class="modal-role-option">
        <input
          type="checkbox"
          value="${e(role.id)}"
          data-role-code="${e(role.code)}"
          ${selectedCodes.includes(role.code) ? "checked" : ""}
        >

        <span>
          <strong>${e(role.libelle)}</strong>
          <code>${e(role.code)}</code>
          <small>${e(role.description || "—")}</small>
        </span>
      </label>
    `).join("");
  }

  function openCreateDialog() {
    editingUser = null;

    $("#userDialogTitle").textContent = "Nouvel utilisateur";
    $("#userDialogSubtitle").textContent =
      "Créez un compte réel et attribuez ses rôles initiaux.";
    $("#saveUser").innerHTML =
      '<i data-lucide="user-plus"></i> Créer le compte';

    $("#userFirstNames").value = "";
    $("#userLastName").value = "";
    $("#userEmail").value = "";
    $("#userEmail").disabled = false;
    $("#userFunction").value = "";
    $("#userPhone").value = "";
    $("#userInitialStatus").value = "ACTIF";

    $("#initialPasswordSection").hidden = false;
    $("#initialRolesSection").hidden = false;
    $("#userStatusCreateField").hidden = false;

    renderModalRoles([]);

    const dialog = $("#userDialog");
    if (!dialog.open) {
      dialog.showModal();
    }

    try {
      generatePassword();
    } catch (error) {
      $("#userInitialPassword").value = "";
      validatePassword();
      state(
        "Le formulaire est ouvert, mais le mot de passe automatique "
        + "n’a pas pu être généré. Saisissez-en un manuellement.",
        true
      );
      console.error("Génération du mot de passe initial :", error);
    }

    icons();
  }

  function openEditDialog() {
    if (!selectedUser) return;

    editingUser = selectedUser;

    $("#userDialogTitle").textContent =
      `Modifier ${displayName(selectedUser)}`;
    $("#userDialogSubtitle").textContent =
      "Le courriel et le mot de passe ne sont pas modifiés ici.";
    $("#saveUser").innerHTML =
      '<i data-lucide="save"></i> Enregistrer';

    $("#userFirstNames").value = selectedUser.prenoms || "";
    $("#userLastName").value = selectedUser.nom || "";
    $("#userEmail").value = selectedUser.email;
    $("#userEmail").disabled = true;
    $("#userFunction").value = selectedUser.fonction || "";
    $("#userPhone").value = selectedUser.telephone || "";

    $("#initialPasswordSection").hidden = true;
    $("#initialRolesSection").hidden = true;
    $("#userStatusCreateField").hidden = true;

    $("#userDialog").showModal();
    icons();
  }

  function generatePassword() {
    const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
    const lower = "abcdefghijkmnopqrstuvwxyz";
    const digits = "23456789";
    const symbols = "!@#$%*+-_=.?";
    const all = upper + lower + digits + symbols;

    const randomIndex = (max) => {
      const values = new Uint32Array(1);
      crypto.getRandomValues(values);
      return values[0] % max;
    };

    const chars = [
      upper[randomIndex(upper.length)],
      lower[randomIndex(lower.length)],
      digits[randomIndex(digits.length)],
      symbols[randomIndex(symbols.length)],
    ];

    while (chars.length < 18) {
      chars.push(all[randomIndex(all.length)]);
    }

    for (let index = chars.length - 1; index > 0; index -= 1) {
      const target = randomIndex(index + 1);
      [chars[index], chars[target]] = [chars[target], chars[index]];
    }

    $("#userInitialPassword").value = chars.join("");
    validatePassword();
  }

  function replaceValidationIcon(container, iconName) {
    if (!container) return;

    const current = container.querySelector("svg, i");
    const icon = document.createElement("i");
    icon.setAttribute("data-lucide", iconName);

    if (current) {
      current.replaceWith(icon);
    } else {
      container.prepend(icon);
    }
  }

  function validatePassword() {
    const value = $("#userInitialPassword").value;

    const lengthOk = value.length >= 12;
    const varietyOk = (
      /[A-Z]/.test(value)
      && /[a-z]/.test(value)
      && /\d/.test(value)
      && /[^A-Za-z0-9]/.test(value)
    );

    const lengthNode = $("#passwordLengthCheck");
    const varietyNode = $("#passwordVarietyCheck");

    lengthNode?.classList.toggle("valid", lengthOk);
    varietyNode?.classList.toggle("valid", varietyOk);

    // Lucide remplace les balises <i> par des <svg>. Une recherche
    // stricte de "i" provoquait donc une exception au deuxième rendu
    // et empêchait l'ouverture du formulaire Nouvel utilisateur.
    replaceValidationIcon(
      lengthNode,
      lengthOk ? "circle-check-big" : "circle"
    );
    replaceValidationIcon(
      varietyNode,
      varietyOk ? "circle-check-big" : "circle"
    );

    icons();

    return lengthOk && varietyOk;
  }

  async function copyText(value) {
    try {
      await navigator.clipboard.writeText(value);
      state("Valeur copiée dans le presse-papiers.");
    } catch {
      state(
        "Copie automatique impossible. Sélectionnez la valeur manuellement.",
        true
      );
    }
  }

  async function saveUser(event) {
    event.preventDefault();
    hideState();

    if (editingUser) {
      try {
        await run(
          () => api.apiPatch(
            `/api/v1/users/${editingUser.id}`,
            {
              nom: $("#userLastName").value.trim() || null,
              prenoms: $("#userFirstNames").value.trim() || null,
              telephone: $("#userPhone").value.trim() || null,
              fonction: $("#userFunction").value.trim() || null,
            }
          ),
          {
            button: event.submitter,
            title: "Utilisateur",
            message: "Mise à jour du compte",
          }
        );

        $("#userDialog").close();
        await loadData();

        selectedUser = users.find(
          (item) => String(item.id) === String(editingUser.id)
        ) || null;

        if (selectedUser) renderDrawer();
        state("Compte utilisateur mis à jour.");
      } catch (error) {
        state(error?.message || "Mise à jour impossible.", true);
      }

      return;
    }

    const password = $("#userInitialPassword").value;
    if (!validatePassword()) {
      state(
        "Le mot de passe initial ne respecte pas les exigences.",
        true
      );
      return;
    }

    const selectedRoles = $$("#modalRoleList input:checked");
    if (!selectedRoles.length) {
      state(
        "Sélectionnez au moins un rôle initial.",
        true
      );
      return;
    }

    try {

const selectedRoleIds = selectedRoles.map(node => node.value);
const created = await run(
  () => api.apiPost(
    "/api/v1/users",
    {
      email: $("#userEmail").value.trim(),
      password,
      nom: $("#userLastName").value.trim() || null,
      prenoms: $("#userFirstNames").value.trim() || null,
      telephone: $("#userPhone").value.trim() || null,
      fonction: $("#userFunction").value.trim() || null,
      statut: $("#userInitialStatus").value,
      role_ids: selectedRoleIds,
    }
  ),
  {
    button: event.submitter || $("#saveUser"),
    title: "Utilisateur",
    message: "Création du compte et attribution des rôles",
    detail: "L’opération est enregistrée dans une seule transaction.",
  }
);

const assigned = selectedRoles.map(checkbox => {
  const role = roles.find(item => String(item.id) === String(checkbox.value));
  return role?.libelle || checkbox.dataset.roleCode;
});
const roleErrors = [];

      $("#userDialog").close();
      await loadData();

      $("#credentialUserName").textContent = displayName(created);
      $("#credentialEmail").textContent = created.email;
      $("#credentialPassword").textContent = password;
      $("#credentialRoleSummary").textContent = assigned.length
        ? `${assigned.length} rôle(s) attribué(s) : ${assigned.join(", ")}`
        : "Aucun rôle attribué";

      const errorNode = $("#credentialRoleErrors");
      errorNode.hidden = !roleErrors.length;
      errorNode.innerHTML = roleErrors.length
        ? `
          <strong>Rôles non attribués</strong>
          <ul>
            ${roleErrors.map((value) => `<li>${e(value)}</li>`).join("")}
          </ul>
        `
        : "";

      $("#credentialDialog").showModal();
      icons();
    } catch (error) {
      state(error?.message || "Création impossible.", true);
    }
  }

  async function saveRoles(event) {
    if (!selectedUser) return;

    const checked = $$("#drawerRoleList input:checked")
      .map((node) => ({
        id: node.value,
        code: node.dataset.roleCode,
      }));

    const checkedCodes = new Set(checked.map((item) => item.code));
    const currentCodes = new Set(selectedUser.roles || []);

    const toAdd = checked.filter(
      (item) => !currentCodes.has(item.code)
    );

    const toRemove = roles.filter(
      (role) =>
        currentCodes.has(role.code)
        && !checkedCodes.has(role.code)
    );

    try {
      await run(
        async () => {
          for (const role of toAdd) {
            await api.apiPost(
              `/api/v1/users/${selectedUser.id}/roles`,
              {
                role_id: role.id,
                motif: "Mise à jour depuis l’administration MVP",
              }
            );
          }

          for (const role of toRemove) {
            await api.apiDelete(
              `/api/v1/users/${selectedUser.id}/roles/${role.id}`
            );
          }
        },
        {
          button: event.currentTarget,
          title: "Habilitations",
          message: "Mise à jour des rôles",
        }
      );

      const userId = selectedUser.id;
      await loadData();

      selectedUser = users.find(
        (item) => String(item.id) === String(userId)
      ) || null;

      if (selectedUser) renderDrawer();
      state("Rôles utilisateur mis à jour.");
    } catch (error) {
      state(error?.message || "Mise à jour des rôles impossible.", true);
    }
  }

  function openStatusDialog() {
    if (!selectedUser) return;

    $("#userStatusDialogTitle").textContent =
      `Statut de ${displayName(selectedUser)}`;

    $("#newUserStatus").value =
      String(selectedUser.statut || "ACTIF").toUpperCase();

    $("#userStatusReason").value = "";
    $("#userStatusDialog").showModal();
    icons();
  }

  async function saveStatus(event) {
    event.preventDefault();
    if (!selectedUser) return;

    const newStatus = $("#newUserStatus").value;
    const reason = $("#userStatusReason").value.trim() || null;

    try {
      await run(
        () => api.apiPatch(
          `/api/v1/users/${selectedUser.id}/status`,
          {
            statut: newStatus,
            motif: reason,
          }
        ),
        {
          button: event.submitter,
          title: "Sécurité utilisateur",
          message: "Application du nouveau statut",
        }
      );

      const userId = selectedUser.id;

      $("#userStatusDialog").close();
      await loadData();

      selectedUser = users.find(
        (item) => String(item.id) === String(userId)
      ) || null;

      if (selectedUser) renderDrawer();
      state(`Statut ${newStatus} appliqué.`);
    } catch (error) {
      state(error?.message || "Changement de statut impossible.", true);
    }
  }

  function resetFilters() {
    filters.search = "";
    filters.role = "";
    filters.status = "";
    filters.sort = "name";

    $("#userSearch").value = "";
    $("#userRoleFilter").value = "";
    $("#userStatusFilter").value = "";
    $("#userSort").value = "name";

    renderUsers();
  }

  function bind() {
    $("#refreshUsers").onclick = async (event) => {
      try {
        await run(
          loadData,
          {
            button: event.currentTarget,
            title: "Administration",
            message: "Actualisation des utilisateurs et rôles",
          }
        );

        state("Administration actualisée.");
      } catch (error) {
        state(error?.message || "Actualisation impossible.", true);
      }
    };

    $("#createUserButton").onclick = openCreateDialog;
    // La délégation résiste aux vues SPA réinjectées et aux remplacements Lucide.
    document.addEventListener("submit", event => {
      if (event.target.id === "userForm") saveUser(event);
      if (event.target.id === "userStatusForm") saveStatus(event);
    }, true);

    $("#generateUserPassword").onclick = generatePassword;
    $("#copyUserPassword").onclick = () =>
      copyText($("#userInitialPassword").value);

    $("#userInitialPassword").oninput = validatePassword;

    $("#userSearch").oninput = (event) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        filters.search = event.target.value.trim();
        renderUsers();
      }, 180);
    };

    $("#userRoleFilter").onchange = (event) => {
      filters.role = event.target.value;
      renderUsers();
    };

    $("#userStatusFilter").onchange = (event) => {
      filters.status = event.target.value;
      renderUsers();
    };

    $("#userSort").onchange = (event) => {
      filters.sort = event.target.value;
      renderUsers();
    };

    $("#resetUserFilters").onclick = resetFilters;

    $("#closeUserDrawer").onclick = closeDrawer;
    $("#userOverlay").onclick = closeDrawer;

    $("#editUser").onclick = () => {
      closeDrawer();
      openEditDialog();
    };

    $("#changeUserStatus").onclick = openStatusDialog;

    $("#saveUserRoles").onclick = saveRoles;

    $$("[data-close-user-dialog]").forEach((button) => {
      button.onclick = () => {
        document.getElementById(
          button.dataset.closeUserDialog
        )?.close();
      };
    });

    $$("[data-copy-credential]").forEach((button) => {
      button.onclick = () => {
        const target = button.dataset.copyCredential;
        copyText(
          target === "email"
            ? $("#credentialEmail").textContent
            : $("#credentialPassword").textContent
        );
      };
    });
  }

  async function bootstrap() {
    try {
      bind();

      currentUser = await api.apiGet("/api/v1/me");

      if (!hasPermission("UTILISATEURS.LIRE")) {
        state(
          "Le compte courant ne possède pas UTILISATEURS.LIRE.",
          true
        );
        $("#createUserButton").hidden = true;
        return;
      }

      $("#createUserButton").hidden =
        !hasPermission("UTILISATEURS.CREER");

      await loadData();
    } catch (error) {
      state(error?.message || "Administration indisponible.", true);
    }

    icons();
  }

  bootstrap();
})();
