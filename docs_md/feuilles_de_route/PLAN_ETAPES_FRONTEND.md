# Plan de raccordement HAUQE Certif

**Dernière consolidation :** 6 août 2026

## Stabilisation récente

- préférences individuelles d'actualisation automatique raccordées au profil ;
- correction du passage Campagne vers Mission dans le formulaire Collecte ;
- ajout des situations « Expirée » et « Audit initial » ;
- retour visuel immédiat des justificatifs sélectionnés ;
- déploiement conditionné à l'application des migrations jusqu'à la tête
  Alembic indiquée dans la feuille d'hébergement.
- avatar de profil repris sur l'écran de verrouillage avec repli vers les
  initiales.

## Prochaine étape hors application

Préparer le squelette Word imprimable du guide global d'utilisation, avec
page de garde, styles, sommaire, chapitres et emplacements de captures. Le
plan détaillé se trouve dans `PLAN_GUIDE_UTILISATION_GLOBAL.md`.

| Étape | Module | État |
|---:|---|---|
| 01 | Dashboard opérationnel | 🟡 recette à consolider |
| 02 | Entreprises | 🟡 tests utilisateur |
| 03 | Organismes certificateurs | 🟡 tests utilisateur |
| 04 | Certifications | 🟡 tests utilisateur |
| 05 | Campagnes → Missions → Collecte | 🟡 tests utilisateur |
| 06 | Vérification documentaire | 🟡 tests utilisateur |
| 07 | Contrôle FUCCS | 🟡 tests utilisateur |
| 08 | Validation + corrections | 🟡 tests utilisateur |
| **09** | **Intégration BNEC** | **🟡 raccordée / tests à faire** |
| **10** | **Classification entreprise / INFC / SNCC** |  🟡 tests utilisateur |
| 11 | Échéances / Alertes / Notifications / Veille |  🟡 tests utilisateur |
| 12 | Tableaux de bord tactique / stratégique / annuel / baromètre / public | **🟡 raccordés aux API — recette utilisateur** |
| 13 | Documents / échanges / décisions / mises à jour | **🟡 raccordée aux API disponibles — recette utilisateur** |
| 14 | Gouvernance / qualité / audit / continuité | **🟡 raccordée — recette sauvegarde/restauration** |
| 15 | Rapports / administration / recette transversale | **🟡 raccordée — recette utilisateur** |

`COLLECTE_COMPLETUDE` reste réservé à Gouvernance / Règles et codification.
La gouvernance, les rapports, le journal d'audit, les référentiels, la publication et les sauvegardes sont raccordés. La recette fonctionnelle et le déploiement du worker backend restent à effectuer.

## Phase de stabilisation des étapes 01 à 15

Les audits V0.1 à V0.4 ont consolidé les étapes 01 à 15. Les modules sont
maintenant en phase de recette transversale, et non plus en attente de
conception.

| Chantier | État |
|---|---|
| Badges de la sidebar alimentés par les API | 🟡 implémenté — recette navigateur |
| Socle commun des modales, fermeture, overflow et zoom | 🟡 consolidé — recette navigateur globale |
| Dossier Validation N1 / N2 | 🟡 reprise visuelle — recette utilisateur |
| Intégration BNEC et plan de codification | 🟡 reprise visuelle — recette utilisateur |
| Calcul INFC sans niveaux publiés | 🟡 corrigé : score calculable, validation bloquée jusqu'au paramétrage des niveaux |
| Veille automatique après intégration BNEC | 🟡 implémentée — recette avec une nouvelle intégration |
| Lisibilité des textes dans Alertes | 🟡 agrandie — recette navigateur |
| Audits V0.1 à V0.4 | ✅ implémentés et documentés — recette utilisateur |

## Recette prioritaire — fiabilité des boutons du menu (03/09/2026)

Un incident transversal a été confirmé : certains boutons affichés dès le
chargement initial d’un écran SPA peuvent exiger plusieurs clics. La correction
de référence est validée sur **Gestion des campagnes** : créer les contrôles
opérationnels après le rendu de leurs lignes, leur attacher un écouteur direct,
éviter `more-button` pour une action métier et exclure les simples ouvertures
de modals du chargeur global.

| Bloc de recette | État | Critère de sortie |
|---|---|---|
| 1. Pilotage | À auditer | Chaque action initiale répond au premier clic. |
| 2. Registre et parcours de collecte | À auditer | Modals, menus de ligne et validations testés avant/après filtre. |

> Mise à jour 23/09/2026 — l'API bloque toute saisie sur une mission sans
> affectation active de l'agent. Lors de l'audit de ce bloc, vérifier que le
> message métier renvoyé en `403` est visible à l'utilisateur ; le filtrage
> visuel des missions personnelles reste une amélioration UX distincte.

> Mise à jour 24/09/2026 — dans **Utilisateurs**, contrôler à l'ouverture de
> « Nouvel utilisateur » que le compteur des rôles actifs est cohérent avec
> le catalogue et que chaque rôle est sélectionnable. Refaire le test après
> rechargement forcé du navigateur.

> Mise à jour 24/09/2026 — dans **Entreprise — formulaire**, activer
> « Identifiants juridiques », saisir et enregistrer un autre identifiant,
> puis le vérifier à la réouverture de la fiche. Cette recette n'est valide
> qu'après application de la migration `f7a1e2c3d4b5`.
| 3. Analyse et veille | À auditer | Aucun bouton d’action ou de relance bloqué après fermeture de modal. |
| 4. Pilotage avancé | À auditer | Filtres, exports et actions de détail stables au premier clic. |
| 5. Administration et référentiels | À auditer | Création, modification, désactivation et publication stables. |
| 6. Audit, qualité et sauvegardes | À auditer | Toutes les actions critiques répondent sans actualisation. |
| 7. Compte et sécurité + NavBar | 🔴 recette bloquante | Des contrôles initiaux restent non réactifs ; audit exhaustif et correction bouton par bouton en cours. |

La progression doit se faire bloc par bloc. Pour chaque écran, consigner le
bouton testé, le résultat au premier clic, le comportement après fermeture du
modal et celui après une erreur API avant de déclarer le bloc conforme.

## Mise à jour Audit V0.4 - 30 juillet 2026

| Domaine | État réel |
|---|---|
| Rapports PDF / Excel / CSV | 🟡 en-tête HAUQE et tableaux ajoutés — recette sur gros volumes |
| Création de compte par courriel | ✅ file SMTP raccordée et test Gmail réussi |
| Référentiels types | ✅ initialisation idempotente, codes proposés et guide |
| Données destinées à la publication | ✅ règle versionnée `PUBLIC_DASHBOARD_INDICATORS` et approbation obligatoire |
| Documents | ✅ téléchargement original et actions protégées contre les clics multiples |
| Échanges organismes / entreprises | ✅ message, envoi différé, échéance et alerte |
| Journal d'audit | ✅ noms lisibles et export institutionnel |
| Sauvegarde système | ✅ exécution backend par `pg_dump`, empreinte SHA-256 |
| Sauvegarde documentaire | ✅ archive des fichiers originaux |
| Sauvegarde complète | ✅ assemblage base et documents |
| Sauvegardes automatiques | ✅ worker quotidien / hebdomadaire / mensuel |
| Restauration | 🟡 test isolé supervisé ; aucune restauration directe en production |

### Services backend requis

Le déploiement doit maintenir deux processus :

1. l'API FastAPI ;
2. `python -m app.tasks.run_background_services`.

Le worker traite la file SMTP chaque minute et vérifie les politiques de
sauvegarde chaque heure. Une seule instance du worker doit être lancée.

### Migration courante

La base PostgreSQL est au niveau Alembic `f4c7d8e9a012`. Cette migration
ajoute le contenu des demandes adressées aux organismes et entreprises.

### Référence des audits

Le registre consolidé est disponible dans :
`audit/corrections/audits-v0.1-a-v0.4-reference.md`.

### Règle INFC

Le calcul du score INFC reste possible lorsque le modèle publié définit la
formule et les pondérations mais pas encore les niveaux institutionnels.
Le résultat est enregistré au statut `CALCULE` avec un niveau vide et
une indication de paramétrage manquant.

La validation définitive reste bloquée tant que le tableau `levels` n'est
pas défini dans la règle versionnée du modèle. Aucun seuil institutionnel
n'est inventé dans le code.

### Veille créée par l'intégration BNEC

Après l'intégration d'une certification validée N2, le système prépare dans
la même transaction :

- l'échéance d'expiration de la certification ;
- le cycle de renouvellement, ouvert 180 jours avant l'expiration ;
- les futurs audits de surveillance encore applicables, estimés aux
  anniversaires de la date d'obtention et marqués `PLANIFIE_A_CONFIRMER` ;
- l'alerte correspondant au seuil déjà atteint (180, 90, 30 jours ou
  expiration).

La synchronisation est idempotente : relancer la même intégration avec les
mêmes données ne doit pas dupliquer les audits, échéances, renouvellements ou
alertes. Les dates d'audit calculées restent modifiables et doivent être
confirmées par un agent.
## Correction authentification — Mot de passe oublié (31/07/2026)

- le formulaire appelle désormais réellement
  `POST /api/v1/auth/password/forgot` ;
- affichage neutre conservé afin de ne pas révéler l’existence d’un compte ;
- le lien reçu ouvre le formulaire de choix du nouveau mot de passe ;
- le routeur accepte `#/mot-de-passe-oublie?token=...` ;
- le nouveau mot de passe est transmis à
  `POST /api/v1/auth/password/reset` ;
- états de chargement, erreurs API, renvoi du lien et confirmation finale
  ajoutés ;
- cache des scripts et styles actualisé.

## Veille par certification — plan libre (24/09/2026)

1. Ouvrir une **certification officielle** puis la **Vue d’ensemble**.
2. La carte **Alertes d’expiration** indique les jalons effectivement
   applicables ; si elle précise « règle générale », aucun réglage local n’a
   encore été enregistré.
3. Avec le rôle **Cellule de veille** ou **Administrateur HAUQE**, cliquer sur
   **Paramétrer**, ajouter les jours avant expiration souhaités puis
   enregistrer. Ne jamais retirer le **Jour J** : il est bloqué par
   l’interface et l’API.
4. Contrôler après l’enregistrement que les jalons affichés correspondent au
   plan. Le changement concerne l’expiration de cette certification et non
   les audits de surveillance ou les autres certifications.

La migration `b4c8d1e2f3a6_certification_expiration_alert_policy.py` est
requise avant utilisation sur un serveur.

## Précréation d’entreprise géolocalisée (24/09/2026)

1. Dans l’étape **Entreprise** d’une nouvelle collecte, rechercher d’abord le
   registre pour éviter un doublon ; utiliser **Précréer** uniquement si aucune
   entreprise n’est trouvée.
2. Saisir l’adresse terrain puis, avec l’accord de la personne utilisant
   l’appareil, cliquer sur **Utiliser ma position**. Latitude et longitude
   restent modifiables manuellement.
3. Après enregistrement, ouvrir la fiche entreprise : le site initial apparaît
   dans **Sites → Implantations enregistrées**. **Voir la carte** n’est affiché
   que lorsque les deux coordonnées sont présentes.
4. Renseigner les coordonnées du déclarant et la description de l’offre : elles
   enrichissent respectivement les contacts actifs et, seulement si vide,
   l’activité principale de l’entreprise.

**Base PostgreSQL modifiée : non ; migration : aucune.**

## Collecter dans une mission affectée (24/09/2026)

1. L'administrateur crée d'abord la campagne, puis la mission depuis
   **Collectes & contrôles**. Il affecte tous les agents concernés ; le bouton
   **Agents** permet d'en ajouter ultérieurement sans modifier les fiches.
2. L'agent ouvre **Nouvelle collecte**, choisit une mission dans sa liste de
   missions affectées et vérifie les informations affichées en lecture seule.
3. Il sélectionne ou précrée l'entreprise, puis poursuit sa propre fiche. Une
   même mission peut ainsi contenir plusieurs collectes d'entreprises.
4. Dès qu'un agent a créé une fiche brouillon, cette fiche lui appartient. Les
   autres agents affectés la consultent seulement ; l'administrateur HAUQE
   peut intervenir si nécessaire.

**Base PostgreSQL modifiée : oui ; migration :
`e1b7c4d9a206_collection_case_ownership.py` ; seed : aucun.**

## Correctif transversal — recherches, listes répétées et boutons (24/09/2026)

- Toute recherche d'un registre doit être effectuée côté API dès qu'elle doit
  dépasser les éléments déjà visibles ; le filtre local seul est insuffisant.
- Une liste d'éléments enfants de fiche doit être dédoublonnée par son `id`,
  puis par une clé métier de secours, et sa sauvegarde doit être monoflux afin
  qu'un clic rapproché ne crée pas deux enregistrements.
- Pour toute action rendue dynamiquement : construire le bouton avec
  `document.createElement`, attacher un écouteur direct unique,
  `preventDefault`, `stopPropagation` et `data-no-action-loader="true"`.
  Lors de la correction d'un bouton, auditer les autres boutons du même bloc.

**Base PostgreSQL modifiée : non ; migration : aucune ; seed : aucun.**

## Offre déclarée → offre entreprise (24/09/2026)

- Déclencher la reprise seulement au moment de la soumission, jamais pendant
  un brouillon.
- Dédupliquer par type, nom et catégorie ; une fiche terrain peut contenir une
  ligne répétée, mais le dossier entreprise ne doit afficher qu'une offre.
- Convertir la saisie libre des marchés en liste et la renseigner dans
  **Marchés cibles** comme dans **Destinations**.
- Documenter toute reprise historique comme une modification de données,
  même lorsqu'aucune migration Alembic n'est nécessaire.

**Base PostgreSQL modifiée : oui, données des offres uniquement ; migration :
aucune ; seed : aucun.**

## Prévention obligatoire des doublons d'offres (24/09/2026)

- Ne jamais dédupliquer seulement avec les champs numériques : volume `0` et
  valeur vide ne rendent pas deux produits différents.
- La clé métier est **type + nom + catégorie** dans une même fiche.
- La protection doit exister dans les trois niveaux : interface, API et index
  PostgreSQL. Les anciennes répétitions sont inactivées avec le statut
  `DOUBLON_ANNULE`, jamais effacées sans autorisation.
- Après une correction de ce type, contrôler à la fois l'affichage, la table
  `offres_declarees` et la rubrique **Offres / produits** de l'entreprise.

**Base PostgreSQL modifiée : oui ; migration :
`h3d9e4f1a607_declared_offer_duplicate_protection.py` ; seed : aucun.**
