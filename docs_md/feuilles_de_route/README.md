# Répertoire unique des feuilles de route HAUQE Certif

**Dernière consolidation :** 3 août 2026

Ce répertoire constitue le point d'entrée unique de la continuité du projet.

## Documents canoniques à maintenir

1. `FEUILLE_DE_ROUTE_HEBERGEMENT_SNGSC.md` : installation, mise à jour,
   migrations, seeds, exploitation et dépannage du serveur Linux.
2. `FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF.md` : état réel du backend,
   décisions techniques, services et endpoints.
3. `FEUILLE_DE_ROUTE_FRONTEND.md` : état réel des pages, parcours, correctifs
   et recette de l'interface.
4. `PLAN_ETAPES_FRONTEND.md` : vue synthétique des étapes fonctionnelles.
5. `PLAN_DEVELOPPEMENT_BACKEND.md` : plan directeur historique du backend.

## Archives de continuité

- `FEUILLE_DE_ROUTE_FRONTEND_v2.md`
- `FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF_v2.md`

Les fichiers suffixés `_v2` sont des instantanés historiques. Ils ne doivent
pas remplacer les trois documents canoniques lors d'un déploiement.

## Règle de mise à jour

Toute modification qui touche une table, une permission, une variable
d'environnement, une tâche serveur ou un parcours frontend doit être reportée
dans les feuilles Backend, Frontend et Hébergement avant mise en production.
