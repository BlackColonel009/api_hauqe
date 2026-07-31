(async function () {
  "use strict";

  const api = await import("/static/js/core/api.js");
  const $ = (selector) => document.querySelector(selector);

  function icons() {
    window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  }

  function tokenFromLocation() {
    const hash = String(location.hash || "");
    const queryIndex = hash.indexOf("?");
    const hashParams = queryIndex >= 0
      ? new URLSearchParams(hash.slice(queryIndex + 1))
      : new URLSearchParams();
    return hashParams.get("token")
      || new URLSearchParams(location.search).get("token")
      || "";
  }

  function showError(node, message) {
    node.textContent = message || "Une erreur est survenue.";
    node.hidden = false;
  }

  function setBusy(button, busy, busyText, idleText) {
    button.disabled = busy;
    const label = button.querySelector("span");
    if (label) label.textContent = busy ? busyText : idleText;
  }

  async function requestReset(email) {
    await api.apiPost(
      "/api/v1/auth/password/forgot",
      { email },
      { auth: false, suppressGlobalAuth: true }
    );
  }

  const token = tokenFromLocation();
  const requestForm = $("#resetRequestForm");
  const requestSuccess = $("#resetSuccess");
  const passwordForm = $("#newPasswordForm");
  const resetComplete = $("#passwordResetSuccess");

  if (token) {
    requestForm.hidden = true;
    requestSuccess.hidden = true;
    passwordForm.hidden = false;
  }

  requestForm.onsubmit = async (event) => {
    event.preventDefault();
    const email = $("#resetEmail").value.trim();
    const error = $("#resetRequestError");
    const button = $("#sendResetLink");
    error.hidden = true;
    setBusy(button, true, "Envoi en cours…", "Envoyer le lien sécurisé");
    try {
      await requestReset(email);
      $("#resetTarget").textContent = email;
      requestForm.hidden = true;
      requestSuccess.hidden = false;
      icons();
    } catch (failure) {
      showError(error, api.describeApiError(failure).message);
    } finally {
      setBusy(button, false, "Envoi en cours…", "Envoyer le lien sécurisé");
    }
  };

  $("#resendReset").onclick = async () => {
    const button = $("#resendReset");
    button.disabled = true;
    try {
      await requestReset($("#resetTarget").textContent.trim());
      button.textContent = "Lien renvoyé";
    } catch (failure) {
      requestSuccess.hidden = true;
      requestForm.hidden = false;
      showError($("#resetRequestError"), api.describeApiError(failure).message);
    } finally {
      setTimeout(() => {
        button.disabled = false;
        button.textContent = "Renvoyer le lien";
      }, 1800);
    }
  };

  passwordForm.onsubmit = async (event) => {
    event.preventDefault();
    const password = $("#resetNewPassword").value;
    const confirmation = $("#resetConfirmPassword").value;
    const error = $("#newPasswordError");
    const button = $("#saveNewPassword");
    error.hidden = true;

    if (password !== confirmation) {
      showError(error, "Les deux mots de passe ne correspondent pas.");
      return;
    }

    setBusy(button, true, "Enregistrement…", "Enregistrer le nouveau mot de passe");
    try {
      await api.apiPost(
        "/api/v1/auth/password/reset",
        { token, new_password: password, confirm_password: confirmation },
        { auth: false, suppressGlobalAuth: true }
      );
      passwordForm.hidden = true;
      resetComplete.hidden = false;
      history.replaceState(null, "", `${location.pathname}${location.search}#/mot-de-passe-oublie`);
      icons();
    } catch (failure) {
      showError(error, api.describeApiError(failure).message);
    } finally {
      setBusy(button, false, "Enregistrement…", "Enregistrer le nouveau mot de passe");
    }
  };

  icons();
})();
