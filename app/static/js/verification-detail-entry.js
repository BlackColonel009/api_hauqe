/*
 * Entrée de la page Vérification.
 *
 * Conserve le contrôleur historique puis aligne l'action « Réouvrir » sur
 * VERIFICATION.CLOTURER. VERIFICATION.AFFECTER reste exclusivement réservé
 * à l'administration des affectations.
 */
(function () {
  "use strict";

  const source = document.createElement("script");
  source.src = "/static/js/verification-detail.js?v=20261004-13";
  source.dataset.pageScript = "true";
  source.onload = async () => {
    try {
      const api = await import("/static/js/core/api.js");
      const user = await api.apiGet("/api/v1/me");
      const dossierId = location.hash.replace(/^#\//, "").split("/")[1];
      const dossier = await api.apiGet(`/api/v1/verifications/${dossierId}`);
      const access = await api.apiGet(`/api/v1/verifications/${dossierId}/write-access`);
      if (!access.modifiable) return;
      if (!dossier?.date_fin || !user?.permissions?.includes("VERIFICATION.CLOTURER")) return;

      const reveal = () => {
        const reopen = document.querySelector("#vdReopen");
        if (reopen) reopen.hidden = false;
      };

      // Le contrôleur principal applique lui-même permissions et affectation.
      reveal();
    } catch {
      // Le contrôleur principal conserve ses propres messages d'erreur.
    }
  };
  document.body.appendChild(source);

  /*
   * La liste des anomalies est redessinée par le contrôleur historique.
   * Ce module remplace l'ancienne fenêtre native de saisie par un modal
   * HAUQE et recrée l'action à chaque rendu : le clic reste immédiatement
   * disponible, même après un changement d'onglet ou un rechargement de liste.
   */
  const anomalyResolution = document.createElement("script");
  anomalyResolution.src = "/static/js/verification-anomaly-resolution.js?v=20260925-3";
  anomalyResolution.dataset.pageScript = "true";
  document.body.appendChild(anomalyResolution);
})();
