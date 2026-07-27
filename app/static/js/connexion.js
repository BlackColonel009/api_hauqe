(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);

  let challengeToken = null;
  let challengeExpiresAt = null;
  let mfaRequired = false;

  const loginForm = $("#loginForm");
  const emailInput = $("#loginEmail");
  const passwordInput = $("#loginPassword");
  const rememberInput = $("#rememberDevice");
  const mfaCodeInput = $("#mfaCode");
  const errorBox = $("#loginError");
  const errorText = $("#loginError span");
  const passwordStep = $("#passwordLoginStep");
  const mfaStep = $("#mfaLoginStep");
  const submitButton = $("#loginSubmit");
  const submitText = $("#loginSubmitText");
  const backButton = $("#backToPasswordStep");
  const mfaExpiry = $("#mfaExpiry");

  function icons() {
    if (window.lucide) {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.8 }
      });
    }
  }

  function showError(message) {
    errorText.textContent = message || "Une erreur est survenue.";
    errorBox.hidden = false;
    icons();
  }

  function clearError() {
    errorText.textContent = "";
    errorBox.hidden = true;
  }

  function setLoading(loading) {
    submitButton.disabled = loading;
    emailInput.disabled = loading || mfaRequired;
    passwordInput.disabled = loading || mfaRequired;
    rememberInput.disabled = loading || mfaRequired;
    mfaCodeInput.disabled = loading || !mfaRequired;

    submitButton.classList.toggle("is-loading", loading);

    if (loading) {
      submitText.textContent = mfaRequired
        ? "Vérification…"
        : "Connexion…";
    } else {
      submitText.textContent = mfaRequired
        ? "Valider le code"
        : "Se connecter";
    }
  }

  function showPasswordStep() {
    mfaRequired = false;
    challengeToken = null;
    challengeExpiresAt = null;
    passwordStep.hidden = false;
    mfaStep.hidden = true;
    mfaCodeInput.value = "";
    mfaExpiry.textContent = "";
    clearError();
    setLoading(false);
    setTimeout(() => emailInput.focus(), 30);
    icons();
  }

  function showMfaStep(result) {
    mfaRequired = true;
    challengeToken = result.challengeToken;
    challengeExpiresAt = result.expiresAt;

    passwordStep.hidden = true;
    mfaStep.hidden = false;

    if (challengeExpiresAt) {
      try {
        const expiry = new Date(challengeExpiresAt);
        mfaExpiry.textContent =
          `Challenge valable jusqu’à ${expiry.toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit"
          })}.`;
      } catch {
        mfaExpiry.textContent =
          "Le challenge MFA est temporaire.";
      }
    } else {
      mfaExpiry.textContent =
        "Le challenge MFA est temporaire.";
    }

    clearError();
    setLoading(false);
    setTimeout(() => mfaCodeInput.focus(), 50);
    icons();
  }

  function destinationAfterLogin() {
    const stored = sessionStorage.getItem(
      "hauqe-return-after-login"
    );

    sessionStorage.removeItem("hauqe-return-after-login");

    if (
      stored
      && stored.startsWith("#/")
      && !stored.startsWith("#/connexion")
    ) {
      return stored;
    }

    return "#/dashboard";
  }

  async function submitCredentials(auth) {
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
      showError(
        "Renseignez l’adresse électronique et le mot de passe."
      );
      return;
    }

    setLoading(true);
    clearError();

    try {
      const result = await auth.login({
        email,
        password,
        remember: rememberInput.checked,
      });

      if (result.mfaRequired) {
        showMfaStep(result);
        return;
      }

      location.hash = destinationAfterLogin();
    } catch (error) {
      const { describeApiError } = await import(
        "/static/js/core/api.js"
      );
      const info = describeApiError(error);

      if (info.status === 423) {
        showError(
          "Cette session doit être déverrouillée avant de poursuivre."
        );
      } else if (info.status === 401) {
        showError(
          "Adresse électronique ou mot de passe incorrect."
        );
      } else if (info.status === 403) {
        showError(
          "Votre compte n’est pas actif ou l’accès est refusé."
        );
      } else if (info.status === 429) {
        showError(
          "Trop de tentatives. Réessayez dans quelques minutes."
        );
      } else {
        showError(info.message);
      }
    } finally {
      if (!mfaRequired) {
        setLoading(false);
      }
    }
  }

  async function submitMfa(auth) {
    const code = mfaCodeInput.value.trim();

    if (!challengeToken) {
      showPasswordStep();
      showError(
        "Le challenge MFA n’est plus disponible. Reconnectez-vous."
      );
      return;
    }

    if (!code) {
      showError(
        "Saisissez votre code MFA ou un code de récupération."
      );
      return;
    }

    setLoading(true);
    clearError();

    try {
      await auth.verifyMfaLogin({
        challengeToken,
        codeOrRecovery: code,
        remember: rememberInput.checked,
      });

      location.hash = destinationAfterLogin();
    } catch (error) {
      const { describeApiError } = await import(
        "/static/js/core/api.js"
      );
      const info = describeApiError(error);

      if (info.status === 401) {
        showError(
          "Code MFA incorrect, expiré ou déjà utilisé."
        );
        mfaCodeInput.select();
      } else {
        showError(info.message);
      }
    } finally {
      setLoading(false);
    }
  }


  function initAuthTypewriter() {
    const target = $("#authTypewriterText");
    if (!target) return;

    const text = "Piloter la conformité.\nAnticiper les risques.";
    const reduceMotion = window.matchMedia?.(
      "(prefers-reduced-motion: reduce)"
    )?.matches;

    if (reduceMotion) {
      target.textContent = text;
      return;
    }

    const TYPE_SPEED = 58;
    const ERASE_SPEED = 28;
    const HOLD_AFTER_TYPED = 1800;
    const HOLD_AFTER_ERASED = 500;

    let index = 0;
    let erasing = false;

    function step() {
      if (!erasing) {
        index += 1;
        target.textContent = text.slice(0, index);

        if (index >= text.length) {
          erasing = true;
          setTimeout(step, HOLD_AFTER_TYPED);
          return;
        }

        setTimeout(step, TYPE_SPEED);
        return;
      }

      index -= 1;
      target.textContent = text.slice(0, Math.max(0, index));

      if (index <= 0) {
        erasing = false;
        setTimeout(step, HOLD_AFTER_ERASED);
        return;
      }

      setTimeout(step, ERASE_SPEED);
    }

    target.textContent = "";
    setTimeout(step, 450);
  }

  document
    .querySelectorAll("[data-toggle-password]")
    .forEach((button) => {
      button.addEventListener("click", () => {
        const input = document.querySelector(
          `#${button.dataset.togglePassword}`
        );
        if (!input) return;

        input.type =
          input.type === "password" ? "text" : "password";

        button.innerHTML = `
          <i data-lucide="${
            input.type === "password" ? "eye" : "eye-off"
          }"></i>
        `;
        icons();
      });
    });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const auth = await import("/static/js/core/auth.js");

    if (mfaRequired) {
      await submitMfa(auth);
    } else {
      await submitCredentials(auth);
    }
  });

  backButton?.addEventListener("click", showPasswordStep);

  // Si un token valide existe déjà, inutile de présenter la page login.
  (async () => {
    try {
      const auth = await import("/static/js/core/auth.js");

      if (auth.getCachedCurrentUser()) {
        location.hash = "#/dashboard";
        return;
      }

      if (
        (await import("/static/js/core/api.js")).hasAccessToken()
      ) {
        const user = await auth.getCurrentUser({ force: true });
        if (user) {
          location.hash = "#/dashboard";
          return;
        }
      }
    } catch {
      // Un token expiré sera géré par le client API.
    }

    showPasswordStep();
  })();

  initAuthTypewriter();
  icons();
})();
