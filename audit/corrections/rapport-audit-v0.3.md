# Rapport de corrections - Audit V0.3

Date : 30 juillet 2026

## Entreprises

- Cause du dysfonctionnement Liste/Grille identifiée : la règle CSS `display:grid` de la vue cartes neutralisait l'attribut HTML `hidden`.
- Ajout d'une règle prioritaire pour masquer réellement la vue inactive.
- Le choix Liste ou Grille continue d'être mémorisé localement.

## Scoring entreprise

- Ajout du guide d'utilisation.
- Le tableau affiche désormais une seule ligne courante par entreprise.
- Les évaluations successives restent enregistrées pour la traçabilité.
- Un clic sur la ligne ouvre un modal présentant les scores, classes, modèles et dates précédents.
- Le texte de la page précise désormais la différence entre résultat courant et historique.

## INFC

- Ajout du guide d'utilisation.
- Une seule ligne courante est affichée par certification.
- Les recalculs précédents restent conservés.
- Un clic sur la ligne ouvre l'historique des scores, niveaux, statuts, modèles et dates.
- Les boutons de validation restent utilisables sans ouvrir involontairement le modal d'historique.

## SNCC

- Ajout du guide d'utilisation.
- Une seule ligne courante est affichée par certification.
- Les classements et périodes antérieurs restent historisés.
- Un clic sur la ligne ouvre le modal des classements précédents.
- Les actions de clôture et de reclassement restent séparées de l'ouverture de l'historique.

## Dossiers de veille

- Ajout du guide d'utilisation.
- La prochaine action d'un dossier crée ou met à jour une échéance de calendrier.
- Une alerte de rappel est affectée au responsable sélectionné.
- Une notification immédiate est ajoutée à son interface.
- Une relance crée deux événements de calendrier lorsque les dates sont renseignées :
  - date d'envoi ;
  - délai de réponse.
- Une relance par courriel est placée dans la file d'envoi :
  - `EN_ATTENTE` si l'envoi doit partir aujourd'hui ;
  - `PLANIFIEE` lorsque la date est future.

Important : cette mise en file ne remplace pas encore le transport SMTP réel. La configuration du service backend d'expédition sera discutée à la fin de l'audit V0.5, avec un essai possible depuis l'adresse email du propriétaire.

## Décisions et actions

- Ajout du guide d'utilisation.
- Ajout d'exemples modifiables dans tous les principaux champs du formulaire.
- Le niveau d'autorité propose les utilisateurs accessibles au rôle connecté grâce à une liste de suggestions.
- La saisie libre de l'autorité reste possible.
- Le modal utilise la présentation moderne existante et comporte une notice sur la diffusion.
- À la création d'une décision, tous les utilisateurs actifs reçoivent une notification dans leur interface.

## Guides livrés

- `guide-scoring-hauqe.pdf`
- `guide-infc-hauqe.pdf`
- `guide-sncc-hauqe.pdf`
- `guide-dossiers-veille-hauqe.pdf`
- `guide-decisions-actions-hauqe.pdf`

Chaque guide tient sur une page, explique la finalité réelle de la page et présente une seule schématisation.

## Contrôles

- Vérification syntaxique des fichiers JavaScript modifiés.
- Compilation Python de l'application.
- Chargement de l'application et de ses routes.
- Rendu PNG et contrôle visuel des cinq guides PDF.
