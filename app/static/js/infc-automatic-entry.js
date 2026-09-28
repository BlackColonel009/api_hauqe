/* Point d'entrée ordonné : moteur automatique, puis écran INFC. */
(function () {
  "use strict";

  function load(source) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = source;
      script.dataset.pageScript = "true";
      script.onload = resolve;
      script.onerror = () => reject(new Error(`Chargement impossible : ${source}`));
      document.body.appendChild(script);
    });
  }

  async function start() {
    try {
      if (!window.HAUQEAutomaticScoringReady) {
        await load("/static/js/automatic-scoring-ui.js?v=20260925-3");
      }
      await window.HAUQEAutomaticScoringReady;
      if (!window.HAUQEAutomaticScoring?.run) throw new Error("Moteur de calcul indisponible.");
      await load("/static/js/infc.js?v=20260927-1");
    } catch (error) {
      const state = document.querySelector("#infcApiState");
      if (state) {
        state.hidden = false;
        state.className = "dashboard-api-state error";
        state.textContent = error.message || "Le moteur automatique n’a pas pu être chargé.";
      }
    }
  }

  start();
})();
