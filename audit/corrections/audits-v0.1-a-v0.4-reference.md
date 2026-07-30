# Référence consolidée des audits HAUQE V0.1 à V0.4

Date de consolidation : 30 juillet 2026

Ce document est le point d'entrée des corrections réalisées. Les rapports détaillés restent conservés séparément dans le même répertoire.

## Audit V0.1 - Socle opérationnel

Référence détaillée : [rapport-audit-v0.1.md](rapport-audit-v0.1.md)

- Tableau de bord, alertes et échéances.
- Synchronisation automatique des certifications, accréditations et échéances.
- Entreprises, certifications et précréations.
- Guides initiaux et modernisation des modals concernés.

État : corrections enregistrées ; les scénarios métier restent à rejouer après toute migration importante.

## Audit V0.2 - Chaîne de traitement

Référence détaillée : [rapport-audit-v0.2.md](rapport-audit-v0.2.md)

- Vérification documentaire et affectations.
- Grille FUCCS sans doublon.
- Validations N1 et N2.
- Intégration BNEC et guides.
- Journalisation des actions sensibles.

État : protections backend et guides enregistrés.

## Audit V0.3 - Scoring, INFC, SNCC et veille

Référence détaillée : [rapport-audit-v0.3.md](rapport-audit-v0.3.md)

- Vue grille des entreprises.
- Une ligne courante par entreprise ou certification.
- Historique complet dans les modals Scoring, INFC et SNCC.
- Dossiers de veille, relances et décisions.
- Rappels, calendrier et notifications.

État : correction de la limite API incluse ; aucun historique métier n'est supprimé.

## Audit V0.4 - Gouvernance, échanges et continuité

Référence détaillée : [rapport-audit-v0.4.md](rapport-audit-v0.4.md)

- Exports institutionnels HAUQE.
- Envoi SMTP des identifiants temporaires.
- Référentiels types et guide.
- Préparation contrôlée des données à publier.
- Documents et échanges programmés.
- Journal d'audit nominatif.
- Sauvegardes système, documents et complètes.
- Worker SMTP et planificateur de sauvegarde.

État : implémentation enregistrée. Le déploiement doit maintenir le worker backend permanent et définir le stockage de production.

## Règles de maintien

- Ne jamais versionner `.env`, les mots de passe, les archives ou les fichiers déposés.
- Appliquer les migrations Alembic avant de démarrer une nouvelle version de l'API.
- Exécuter une seule instance du worker de fond.
- Tester une restauration sur un environnement isolé avant toute opération de production.
- Mettre à jour le rapport de version lorsqu'une correction est modifiée ou retirée.
