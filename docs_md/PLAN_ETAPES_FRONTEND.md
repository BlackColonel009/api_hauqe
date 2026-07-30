# Plan de raccordement HAUQE Certif

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
