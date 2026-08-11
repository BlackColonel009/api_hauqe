# Répertoire unique des feuilles de route HAUQE Certif

**Dernière consolidation :** 11 août 2026

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
6. `PLAN_GUIDE_UTILISATION_GLOBAL.md` : plan validé du futur manuel Word
   imprimable destiné aux utilisateurs du système.

## Archives de continuité

- `FEUILLE_DE_ROUTE_FRONTEND_v2.md`
- `FEUILLE_DE_ROUTE_BACKEND_HAUQE_CERTIF_v2.md`

Les fichiers suffixés `_v2` sont des instantanés historiques. Ils ne doivent
pas remplacer les trois documents canoniques lors d'un déploiement.

## Règle de mise à jour

Toute modification qui touche une table, une permission, une variable
d'environnement, une tâche serveur ou un parcours frontend doit être reportée
dans les feuilles Backend, Frontend et Hébergement avant mise en production.

## Point de reprise - 11 août 2026

Les correctifs Collecte, situations déclarées, préférences de rafraîchissement
et affichage de l'avatar sur l'écran de verrouillage sont réalisés dans le
code local. Une version rédigée, professionnelle et modifiable du guide global
d'utilisation est disponible dans
`output/docx/Guide_global_utilisation_SNGSC_HAUQE_v2.docx`, sans captures
d'écran. La prochaine action documentaire est sa relecture métier et
l'insertion des captures nettoyées par la HAUQE, selon
`PLAN_GUIDE_UTILISATION_GLOBAL.md`.

Les correctifs de sécurité d'authentification sont réalisés localement et
documentés dans les feuilles Frontend et Backend :

- purge des caches utilisateur/profil avec le token afin d'éviter la boucle
  connexion → tableau de bord → connexion après expiration ou révocation ;
- exclusion des formulaires de connexion, MFA, mot de passe oublié et session
  sécurisée du chargeur automatique afin qu'un échec ne bloque plus le bouton ;
- changement de mot de passe : toutes les sessions, y compris la session
  courante, sont révoquées ; l'utilisateur est renvoyé vers la connexion ;
- notification interne et courriel de sécurité HAUQE générés sans jamais
  transmettre le mot de passe en clair ;
- signature de courriel institutionnelle configurable via `HAUQE_CONTACT_*`
  dans `.env`.

Recette à exécuter avant déploiement : tester un mot de passe erroné, un code
MFA erroné, un code de session sécurisée erroné, l'expiration d'un token et un
changement de mot de passe suivi d'une reconnexion avec le nouveau mot de
passe.
