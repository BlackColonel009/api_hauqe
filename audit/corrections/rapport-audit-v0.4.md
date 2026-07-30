# Rapport de corrections - Audit V0.4

Date : 30 juillet 2026

## Rapports

- Ajout de l'en-tête HAUQE et de la définition « Haute Autorité de la Qualité et de l'Environnement ».
- Ajout du titre, de la date, du demandeur et du nombre d'enregistrements.
- Présentation tabulaire professionnelle pour PDF, Excel et CSV.

## Administration

- Ajout de l'option d'envoi des identifiants temporaires lors de la création d'un compte.
- Placement du courriel dans la file SMTP transactionnelle.
- Le mot de passe reste absent du journal d'audit et son contenu est effacé de la notification après l'envoi.
- Configuration SMTP Gmail contrôlée par un envoi isolé réussi.

## Référentiels et nomenclatures

- Ajout du guide PDF.
- Ajout d'un référentiel type couvrant les principaux statuts, domaines, décisions, échéances, risques et niveaux de confidentialité.
- L'initialisation est idempotente : elle n'écrase pas les référentiels existants.
- Proposition de codes incrémentés et modifiables.
- Modal moderne pour créer un référentiel.
- Correction du bouton crayon de modification d'une valeur.

## Règles, codification et publication

- Ajout de l'onglet « Données à publier ».
- Sélection des indicateurs agrégés autorisés.
- Identification et justification obligatoire des champs nominatifs proposés.
- Création d'un brouillon versionné `PUBLIC_DASHBOARD_INDICATORS`.
- La demande de publication, son approbation et sa publication restent obligatoires.
- Le tableau public conserve une liste blanche technique : une donnée nominative n'est jamais exposée directement par erreur.

## Documents

- Conservation stricte du fichier original lors du téléchargement : contenu, format et nom.
- Correction des gestionnaires accumulés lors des navigations SPA.
- Désactivation temporaire des boutons pendant les requêtes pour empêcher les clics multiples.

## Échanges avec les organismes

- Formulaire moderne avec destinataire, canal, objet, message, date d'envoi et échéance.
- Ajout du contenu de la demande au modèle et à l'API.
- Migration appliquée : `f4c7d8e9a012_confirmation_message.py`.
- Un courriel est placé dans la file pour un envoi immédiat ou futur.
- L'échéance de réponse alimente le calendrier et crée une alerte.

## Journal d'audit

- Résolution du nom et du courriel de l'utilisateur au lieu d'un UUID tronqué.
- Export professionnel avec en-tête HAUQE, demandeur, date et tableau.

## Sauvegardes

- Trois périmètres : `SYSTEME`, `DOCUMENTS`, `COMPLETE`.
- La sauvegarde système utilise `pg_dump`.
- La sauvegarde documentaire archive les fichiers déposés sans les transformer.
- La sauvegarde complète assemble base et documents.
- Contrôle d'intégrité SHA-256, taille, emplacement, statut et audit.
- Exécution backend indépendante de la page après création de la route.
- Modal de progression avec couleurs rouge, orange, jaune, bleu et vert.
- Planificateur quotidien, hebdomadaire et mensuel idempotent.
- Worker permanent : `python -m app.tasks.run_background_services`.

## Contrôles effectués

- Compilation Python de `app` et des migrations : réussie.
- Contrôle syntaxique des scripts JavaScript modifiés : réussi.
- Migration PostgreSQL au niveau `f4c7d8e9a012` : appliquée.
- Détection de `pg_dump` : réussie.
- Chargement SMTP et envoi Gmail isolé : réussis.

## Exploitation serveur

Le serveur doit exécuter deux processus :

1. l'API FastAPI ;
2. `python -m app.tasks.run_background_services`.

Le second traite la file SMTP chaque minute et contrôle les politiques de sauvegarde chaque heure. Une seule instance de ce worker doit être active.
