# Suivi des livrables — Projet HAUQE Certif

> Registre de pilotage des livrables techniques, fonctionnels, méthodologiques et de transfert.
>
> Date de création : 17 juillet 2026  
> Dernière mise à jour : 23 juillet 2026  
> Référence de continuité : `PASSATION_PROJET_HAUQE_CERTIF.md`

## 1. Objet du document

Ce document permet de suivre la préparation, la réalisation, la validation et la remise des livrables du projet HAUQE Certif.

Il doit être actualisé après chaque avancée importante. Un livrable ne peut être indiqué comme validé que lorsqu'une validation identifiable de la HAUQE, de GFA ou de l'autorité compétente a été reçue.

## 2. Règles de suivi

### Statuts

| Statut | Signification |
|---|---|
| À démarrer | Aucun contenu formel n'a encore été produit |
| En préparation | Collecte des informations, analyse ou rédaction en cours |
| Brouillon produit | Une première version exploitable existe |
| En revue interne | Vérifications techniques et fonctionnelles en cours |
| Soumis pour validation | Livrable transmis à l'autorité de validation |
| À corriger | Retours reçus et corrections attendues |
| Validé | Validation formelle obtenue et enregistrée |
| Livré | Version finale remise avec ses preuves de transmission |

### Informations à conserver pour chaque livrable

- responsable de production ;
- contributeurs et validateurs ;
- version et date de mise à jour ;
- fichiers constituant le livrable ;
- éléments de preuve ou critères d'acceptation ;
- décisions reçues et points restant ouverts ;
- date de soumission, de validation et de remise ;
- observations et prochaines actions.

## 3. Tableau de synthèse

| ID | Livrable | Catégorie | Statut actuel | Fichier principal prévu | Validation attendue |
|---|---|---|---|---|---|
| LIV-01 | Rapport de cadrage technique et méthodologique | Cadrage | En préparation | `RAPPORT_CADRAGE_TECHNIQUE_METHODOLOGIQUE.md` | HAUQE / GFA |
| LIV-02 | Architecture fonctionnelle et schéma de conception de la base | Conception | Brouillon produit | `MCD_HAUQE_CERTIF.md` et `output/pdf/MCD_HAUQE_CERTIF_POWERDESIGNER.pdf` | HAUQE / référents métier et technique |
| LIV-03 | Base de données nationale des entreprises certifiées opérationnelle | Réalisation | À démarrer | Code, migrations et dossier technique | Recette technique et fonctionnelle |
| LIV-04 | Tableaux de bord et outils de suivi intégrés et fonctionnels | Réalisation | Brouillon produit | Frontend existant et futures API de pilotage | Recette fonctionnelle |
| LIV-05 | Rapport d'intégration et de structuration des données | Données | À démarrer | `RAPPORT_INTEGRATION_STRUCTURATION_DONNEES.md` | HAUQE / GFA |
| LIV-06 | Fiches et formulaires harmonisés de collecte | Collecte | Brouillon produit | Fiche officielle, formulaire frontend et dictionnaire de données | HAUQE |
| LIV-07 | Grilles techniques de contrôle et de vérification | Contrôle | Brouillon produit | Grille des 7 domaines et 28 critères | HAUQE |
| LIV-08 | Système de codification et de classification | Référentiels | Brouillon produit | `SYSTEME_CODIFICATION_CLASSIFICATION.md` | HAUQE |
| LIV-09 | Outils de scoring et mécanismes de suivi | Suivi | Brouillon produit | Module scoring, règles et mécanismes d'alerte | HAUQE |
| LIV-10 | Rapport technique sur les mécanismes de gestion et de contrôle | Documentation technique | À démarrer | `RAPPORT_MECANISMES_GESTION_CONTROLE.md` | HAUQE / GFA |
| LIV-11 | Supports de formation et guides d'utilisation | Formation | En préparation | `GUIDE_UTILISATION.md` et supports de formation | HAUQE |
| LIV-12 | Sessions de formation et démonstrations pratiques | Formation | À démarrer | Programme, listes de présence et comptes rendus | HAUQE / participants |
| LIV-13 | Rapport de transfert de compétences et de renforcement des capacités | Transfert | À démarrer | `RAPPORT_TRANSFERT_COMPETENCES.md` | HAUQE / GFA |
| LIV-14 | Rapport final consolidé avec recommandations | Clôture | À démarrer | `RAPPORT_FINAL_CONSOLIDE.md` | HAUQE / GFA |

## 4. Fiches détaillées des livrables

### LIV-01 — Rapport de cadrage technique et méthodologique

**Statut :** En préparation

**Contenu attendu :**

- contexte, objectifs et périmètre de la mission ;
- acteurs, responsabilités et gouvernance ;
- analyse des besoins et contraintes ;
- démarche méthodologique ;
- choix techniques FastAPI, PostgreSQL, Jinja2 et JavaScript ;
- stratégie de collecte, validation, intégration et contrôle ;
- sécurité, sauvegarde, audit et protection des données ;
- planning, risques, hypothèses et dépendances ;
- critères de recette et de validation des livrables.

**Sources existantes :**

- `PASSATION_PROJET_HAUQE_CERTIF.md` ;
- `CONTEXTE_COMMUNICATIONS.md` ;
- TDR et documents contractuels ;
- fiche unique HAUQE/FUCCS/01 ;
- règles métier soumises à validation.

**Prochaine action :** produire la table des matières puis rapprocher le cadrage des exigences contractuelles.

### LIV-02 — Architecture fonctionnelle et schéma de conception de la base

**Statut :** En préparation

**Sous-livrables prévus :**

1. cartographie des modules et acteurs ;
2. parcours métier et transitions de statuts ;
3. modèle conceptuel de données (MCD) ;
4. dictionnaire conceptuel des données ;
5. modèle logique de données (MLD) ;
6. schéma physique PostgreSQL (MPD) ;
7. architecture des API FastAPI ;
8. matrice des rôles et permissions ;
9. règles d'intégrité, d'historisation et d'audit.

**Décisions de conception déjà retenues :**

- relations multiples modélisées par des entités ou associations dédiées ;
- conservation des révisions de collecte et des valeurs déclarées ;
- versionnement des grilles, règles et formules de scoring ;
- historisation des statuts, affectations, décisions et alertes ;
- séparation entre données officielles, données déclarées et preuves documentaires ;
- identifiants métier distincts des identifiants techniques ;
- archivage ou désactivation au lieu de la suppression des données déjà utilisées.

**Chantier actif : Modèle conceptuel de données**

Le MCD sera élaboré à partir de la fiche officielle, des 24 pages frontend, du parcours collecte-validation-contrôle et des règles métier. Les entités et cardinalités proposées resteront marquées comme provisoires jusqu'à validation.

Le plan d'exécution détaillé est enregistré dans `PLAN_DEVELOPPEMENT_BACKEND.md`. Il tient compte du parcours complet désormais validé : collecte, vérification, contrôle FUCCS, validation, intégration BNEC, classification entreprise, INFC, SNCC et veille.

Une première version du MCD est produite dans `MCD_HAUQE_CERTIF.md`. Elle décrit 14 domaines, leurs entités, associations, cardinalités, règles transversales et points d'arbitrage.

**Prochaine action :** relire les cardinalités, établir le dictionnaire conceptuel puis dériver le MLD.

### LIV-03 — Base de données nationale opérationnelle

**Statut :** À démarrer

**Éléments de preuve attendus :**

- instance PostgreSQL configurée ;
- migrations Alembic versionnées ;
- contraintes, index et données de référence ;
- API FastAPI documentée ;
- authentification et permissions ;
- tests automatisés et résultats de recette ;
- procédure de sauvegarde et restauration ;
- documentation d'installation et d'exploitation.

### LIV-04 — Tableaux de bord et outils de suivi

**Statut :** Brouillon produit côté frontend ; backend à réaliser

**Éléments concernés :** tableau de bord, alertes, échéances, collecte, validation, contrôle, scoring et rapports.

**Reste à faire :** remplacer les données simulées par les API, appliquer les permissions, fiabiliser les calculs et tester les exports.

### LIV-05 — Rapport d'intégration et de structuration des données

**Statut :** À démarrer

**Contenu attendu :** sources reçues, contrôles de qualité, règles de nettoyage, correspondances de champs, dédoublonnage, anomalies, données rejetées ou corrigées, statistiques d'intégration et traçabilité des imports.

### LIV-06 — Fiches et formulaires harmonisés de collecte

**Statut :** Brouillon produit ; validation métier requise

**État actuel :** formulaire numérique en six étapes, collections structurées de produits, marchés et certifications, justificatifs, consentement et signature.

**Point bloquant de validation :** rapprocher chaque champ de la version officielle communiquée par M. Nyanutse et confirmer les champs obligatoires, conditionnels et répétables.

### LIV-07 — Grilles techniques de contrôle et de vérification

**Statut :** Brouillon produit ; validation métier requise

**État actuel :** proposition de 28 critères répartis en sept domaines, notation de 0 à 2 et score brut sur 56.

**À confirmer :** libellés, preuves exigées, portée des notes, commentaires obligatoires, seuils, décisions et réouverture d'un contrôle.

### LIV-08 — Système de codification et de classification

**Statut :** Brouillon produit ; validation métier requise

**Contenu attendu :** nomenclature des entités, normes et produits ; formats des codes ; règles de séquence ; unicité ; versionnement ; publication ; compatibilité avec les références COTAG et autres certifications non ISO.

### LIV-09 — Outils de scoring et mécanismes de suivi

**Statut :** Brouillon produit ; formules provisoires

**État actuel :** score brut sur 56, indice provisoire sur 100, comparaison historique, actions prioritaires, alertes et échéances.

**À confirmer :** pondérations, formule, seuils, arrondis, niveaux de conformité, décisions associées et droits de consultation.

### LIV-10 — Rapport technique sur les mécanismes de gestion et de contrôle

**Statut :** À démarrer

**Contenu attendu :** gouvernance des données, circuits de validation, gestion des versions, contrôle documentaire, scoring, alertes, échéances, actions correctives, audit, sécurité, rapports et administration fonctionnelle.

### LIV-11 — Supports de formation et guides d'utilisation

**Statut :** En préparation

**État actuel :** `GUIDE_UTILISATION.md` existe et doit être enrichi à chaque fonctionnalité backend.

**Supports à produire :** guide utilisateur par profil, guide administrateur, guide technique, support de présentation, exercices pratiques et aide-mémoire.

### LIV-12 — Sessions de formation et démonstrations pratiques

**Statut :** À démarrer

**Preuves attendues :** programme, convocations, listes de présence, supports utilisés, exercices, évaluations, photos si autorisées, difficultés rencontrées et procès-verbal ou compte rendu.

### LIV-13 — Rapport de transfert de compétences

**Statut :** À démarrer

**Contenu attendu :** bénéficiaires, compétences visées, activités réalisées, acquis, difficultés, autonomie atteinte, ressources remises, besoins complémentaires et recommandations de maintien des compétences.

### LIV-14 — Rapport final consolidé de mission

**Statut :** À démarrer

**Contenu attendu :** rappel du mandat, méthodologie, réalisations, résultats, difficultés, écarts, état des livrables, résultats des tests et formations, transfert, recommandations techniques et opérationnelles, annexes et procès-verbaux de validation.

## 5. Registre des validations

| Date | Livrable | Version | Transmis à | Décision | Preuve ou référence | Actions |
|---|---|---|---|---|---|---|
| À renseigner | — | — | — | — | — | — |

## 6. Registre des modifications

| Date | Livrable concerné | Modification | Auteur | Effet sur le projet |
|---|---|---|---|---|
| 17/07/2026 | Tous | Création du registre initial des 14 livrables | Équipe projet | Mise en place du suivi centralisé |
| 23/07/2026 | LIV-02 et LIV-03 | Ajout du plan de développement PostgreSQL/FastAPI aligné sur RM-01 à RM-51 | Équipe projet | Démarrage formel de la conception backend |
| 23/07/2026 | LIV-02 et LIV-03 | Adoption de l'architecture `backend/app` avec routes, repositories, services, règles, permissions, audit et tâches | Équipe projet | Convention officielle d'organisation du backend |
| 23/07/2026 | LIV-02 | Production de la version 0.1 du MCD HAUQE Certif | Équipe projet | Base conceptuelle disponible pour relecture et dérivation du MLD |
| 23/07/2026 | LIV-02 | Création du schéma MCD sur une page dans FigJam BenLo | Équipe projet | Schéma modifiable et exportable en PDF pour les livrables |
| 23/07/2026 | LIV-02 | Production du PDF A3 de 11 pages : MCD contracté et dix planches détaillées | Équipe projet | Livrable de conception prêt pour revue GFA/HAUQE |
| 23/07/2026 | LIV-02 | Refonte du MCD détaillé en notation Merise proche de PowerDesigner : entités, attributs, associations et cardinalités graphiques | Équipe projet | Version 0.2 produite en PDF A3 multipage pour revue métier |

## 7. Prochaines priorités

1. construire et valider progressivement le MCD ;
2. produire le dictionnaire conceptuel des données ;
3. rapprocher le MCD de tous les champs de la fiche officielle ;
4. formaliser les règles de gestion et cardinalités ;
5. dériver le MLD puis le schéma PostgreSQL ;
6. compléter le rapport de cadrage à partir des décisions validées ;
7. mettre à jour ce registre après chaque avancée ou validation.
