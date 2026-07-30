# Rapport de corrections - Audit V0.1

Date : 30 juillet 2026

## Périmètre appliqué

Ce rapport couvre uniquement les constats communiqués pour les pages Tableau de bord, Alertes, Échéances, Entreprises et Certifications.

## Tableau de bord

- Remplacement des anciens pictogrammes d'aide par des icônes d'information modernes aux couleurs du thème.
- Agrandissement de la zone cliquable et gestion directe de l'événement pointeur.
- Ajout des états d'accessibilité `aria-expanded` et d'une infobulle explicite.

## Alertes

- La ligne indique maintenant clairement l'action `Voir le détail`.
- Le clic sélectionne l'alerte et affiche sa fiche de traitement.
- Le bouton `Ouvrir la ressource` reste proposé lorsque le backend fournit une route vers le dossier source.
- Ajout du bouton `Guide d'utilisation`.
- Nouveau guide PDF d'une page avec une seule schématisation légendée :
  `app/static/docs/guide-alertes-hauqe.pdf`.

## Échéances

- Ajout de propositions rapides pour le type, la priorité et le titre, tout en conservant la saisie libre.
- Ajout d'un exemple de description opérationnelle.
- Remplacement du détail en bannière par un petit modal moderne.
- Refonte du modal `Terminer` / `Annuler` avec motif obligatoire et rappel de traçabilité.
- Conservation du motif de clôture dans la nouvelle colonne `motif_cloture`.
- Affichage dans le calendrier :
  - `Exécutée avec motif : ...` pour une échéance terminée ;
  - `Annulée avec motif : ...` pour une échéance annulée.
- Ajout de la migration Alembic `e1f0a2b3c4d5_deadline_closure_reason.py`.

## Alimentation automatique des échéances et alertes

Le raccordement BNEC existait déjà : après intégration validée, le moteur crée l'expiration, le renouvellement, les audits de surveillance et les alertes selon les seuils 180 / 90 / 30 jours.

La V0.1 étend ce fonctionnement :

- création directe d'une certification : synchronisation automatique ;
- modification des dates d'une certification : mise à jour de l'échéance active au lieu de créer un doublon ;
- création ou modification d'une accréditation avec date d'expiration : synchronisation automatique ;
- création des alertes correspondant au seuil temporel atteint ;
- les modifications d'entreprise ou d'organisme restent visibles par les libellés résolus depuis les données courantes ;
- les certifications déclarées dans Collecte alimentent le calendrier après leur validation et leur intégration BNEC, afin de ne pas publier des échéances provenant de données encore non validées.

## Entreprises

- Réparation du basculement Liste / Grille.
- Prise en charge des valeurs `cards` et `grid`.
- Mémorisation locale du mode d'affichage choisi.

## Certifications

- Ajout d'une proposition d'identifiant au format `HAUQE-CERT-AAAA-XXXXXX`.
- Ajout de la précréation d'un référentiel/norme absent depuis le formulaire.
- Le code, l'intitulé et le domaine/référentiel peuvent être saisis librement.
- La nouvelle norme est enregistrée avec le statut `A_VERIFIER`, puis sélectionnée automatiquement.
- Ajout de la précréation d'un organisme certificateur absent.
- L'organisme est créé avec le statut `A_VERIFIER`, puis sélectionné automatiquement.
- Réparation de l'ajout d'une accréditation depuis l'étape Organisme.
- L'accréditation créée est sélectionnée immédiatement.

## Contrôles réalisés

- Vérification syntaxique des fichiers JavaScript modifiés avec Node.js.
- Compilation Python de `app` et de la migration Alembic.
- Génération et rendu PNG du guide PDF Alertes avec Poppler.
- Contrôle visuel du rendu PDF : une page, lisible, sans chevauchement ni contenu tronqué.
- La suite automatisée n'a pas pu être lancée : `pytest` n'est installé ni dans l'environnement virtuel du projet ni dans le runtime Python fourni.

## Fichiers principaux concernés

- `app/static/js/app.js`
- `app/static/js/alertes.js`
- `app/static/js/echeances.js`
- `app/static/js/entreprises.js`
- `app/static/js/certification-form.js`
- `app/services/veille_service.py`
- `app/services/organismes_certifications_service.py`
- `app/repositories/veille_repository.py`
- `app/models/echeance.py`
- `app/schemas/veille.py`
- `app/schemas/organismes_certifications.py`
- `app/routes/api/v1/organismes_certifications.py`
- `alembic/versions/e1f0a2b3c4d5_deadline_closure_reason.py`
