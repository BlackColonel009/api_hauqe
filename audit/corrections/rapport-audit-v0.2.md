# Rapport de corrections - Audit V0.2

Date : 30 juillet 2026

## Périmètre

Ce rapport couvre uniquement les constats transmis pour Vérifications, Grille de contrôle FUCCS, Validations et Intégration BNEC.

## Vérifications

- Ajout du guide PDF simple et de son bouton dans l'en-tête.
- Confirmation de la protection existante contre un second dossier ouvert pour une même fiche.
- Renforcement contre les doubles clics concurrents avec verrouillage de la fiche pendant l'ouverture.
- Confirmation de la protection contre une seconde affectation active du même vérificateur au même dossier.
- Validation de la cohérence des dates :
  - la fin ne peut pas précéder le début ;
  - l'échéance ne peut pas précéder le début.
- À la création et à la modification d'une affectation, chaque date renseignée alimente ou met à jour le calendrier :
  - début de l'affectation ;
  - fin prévue ;
  - échéance de vérification.
- Une date retirée lors d'une modification annule proprement l'échéance correspondante.
- Chaque date validée crée ou met à jour une alerte affectée au vérificateur.
- Deux notifications sont préparées pour le vérificateur :
  - notification immédiate dans l'interface ;
  - notification email placée dans la file d'envoi.
- Les créations et modifications d'affectation restent journalisées.

## Grille de contrôle FUCCS

- Ajout du guide PDF simple et de son bouton dans l'en-tête.
- Confirmation du fonctionnement anti-doublon :
  - `Démarrer` ou `Reprendre` retourne le contrôle déjà lié au dossier ;
  - un double clic est sérialisé par verrouillage du dossier ;
  - `Réouvrir` modifie le contrôle finalisé existant et ne crée aucune nouvelle ligne.
- Ajout de l'événement d'audit `FUCCS_CONTROL_RESUME` lorsqu'un contrôle existant est repris.
- Confirmation de la journalisation existante pour :
  - création et modification des grilles, rubriques et critères ;
  - saisie et mise à jour des notes ;
  - création et mise à jour des constats ;
  - finalisation ;
  - réouverture motivée.

## Validations

- Ajout du guide PDF simple et de son bouton dans l'en-tête.
- Confirmation de la déduplication de la file par fiche.
- Confirmation du blocage d'une nouvelle décision lorsqu'une décision favorable active existe déjà au même niveau.
- Renforcement contre deux décisions concurrentes du même niveau par verrouillage de la fiche.
- Les décisions ajournées restent historisées et doivent suivre le circuit de correction.

## Intégration BNEC

- Ajout du guide PDF simple et de son bouton dans l'en-tête.
- Le guide décrit la file N2, le plan et la codification, l'exécution transactionnelle et la traçabilité.
- Le raccordement déjà présent vers les audits, renouvellements, échéances et alertes après intégration est rappelé dans le guide.

## Guides livrés

- `guide-verifications-hauqe.pdf`
- `guide-controle-fuccs-hauqe.pdf`
- `guide-validations-hauqe.pdf`
- `guide-integration-bnec-hauqe.pdf`

Chaque guide tient sur une page, contient une seule schématisation de l'interface et une procédure courte.

## Contrôles

- Compilation Python réussie.
- Vérification syntaxique JavaScript réussie.
- Import de l'application et chargement des routes réussis.
- Les quatre PDF ont été rendus en PNG et contrôlés visuellement :
  aucune coupure, aucun chevauchement et aucune page supplémentaire.
