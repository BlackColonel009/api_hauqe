# Guide d'utilisation — HAUQE Certif

> Document de travail évolutif. Il doit être complété et illustré après validation définitive des maquettes et des règles métier.

## 1. Objet du guide

Ce guide présente les rôles, écrans, boutons, statuts et circuits de traitement du système national de gestion et de suivi des certifications.

Sur le **Tableau de bord**, cliquer sur une carte d'indicateur ouvre le registre correspondant. Les actions prioritaires ouvrent Alertes, Validations ou Échéances selon leur nature. Une ligne de certification récente ouvre son dossier ; son bouton à trois points propose aussi l'entreprise et l'échéance associées.

## 2. Profils utilisateurs prévus

- **Administrateur HAUQE** : paramétrage, utilisateurs, supervision et accès global.
- **Coordonnateur ou superviseur** : campagnes, missions, affectations et suivi des délais.
- **Agent de collecte** : préparation des missions, saisie des fiches et traitement des corrections.
- **Contrôleur ou validateur HAUQE** : examen des fiches, grille des 28 critères et décision.
- **Consultation ou direction** : tableaux de bord, indicateurs, dossiers et rapports autorisés.

Les droits définitifs devront être validés avant le développement de l'API d'authentification.

## 3. Parcours d'une collecte

1. Dans **Collectes & contrôles**, l'agent clique sur **Nouvelle collecte**.
2. Il remplit le formulaire numérique : mission, entreprise, activités, produits, marchés, certifications et justificatifs. Les boutons **Ajouter un produit** et **Ajouter une certification** créent des enregistrements distincts conservés dans le brouillon. Pour chaque certification, il précise notamment le référentiel, l'organisme, le numéro, la portée, les dates, le statut et la disponibilité de la copie.
3. Il peut utiliser **Enregistrer le brouillon** pour poursuivre ultérieurement.
4. La dernière étape contrôle les informations primordiales et bloque une soumission incomplète. Les 28 critères et le score sont réservés aux étapes Validation et Contrôle.
5. Il clique sur **Soumettre à la HAUQE** lorsque la fiche est complète.
6. La fiche arrive dans **Validations > Non affectées**.
7. Un superviseur utilise **Affecter les dossiers** pour désigner un validateur.
8. La fiche apparaît dans **Mes validations** du validateur choisi.
9. Le validateur contrôle la complétude puis clique sur **Recevable — démarrer le contrôle** pour ouvrir la **Grille de contrôle**.
10. Il note les 28 critères de 0 à 2, ajoute les constats et motive sa décision.
11. Il valide le dossier ou le retourne à l'agent avec les corrections attendues.
12. En cas de retour, l'agent modifie la fiche puis la soumet à nouveau.

## 4. Barème de la grille de contrôle

- **0 — Non conforme** : exigence absente, preuve invalide ou écart majeur.
- **1 — Partiellement conforme** : exigence partiellement satisfaite ou preuve incomplète.
- **2 — Conforme** : exigence satisfaite et preuve vérifiable.

La grille contient 28 critères et produit un score maximal de 56. Les seuils de décision devront être confirmés par la HAUQE.

## 5. Consultation du scoring

Après la finalisation du contrôle, l'utilisateur autorisé ouvre **Scoring** dans le menu Analyse. Il sélectionne l'entreprise et le contrôle à consulter.

La page distingue :

- le **score brut sur 56**, directement issu des 28 critères ;
- le **pourcentage du contrôle** ;
- l'**indice global sur 100**, calculé avec des pondérations provisoires ;
- la performance par domaine ;
- l'évolution par rapport aux contrôles précédents ;
- les actions correctives prioritaires.

Les pondérations, seuils et décisions proposées affichés dans la maquette devront être validés par la HAUQE avant toute utilisation réglementaire.

### Planifier le suivi d'un résultat

Depuis les actions prioritaires du scoring, **Planifier le suivi** ouvre le calendrier avec une nouvelle échéance préremplie. L'utilisateur vérifie l'entreprise, le type, la date, le responsable et l'action attendue avant l'enregistrement.

Dans le calendrier :

- un clic sur un événement ouvre son détail et permet sa modification ;
- un clic sur une ligne de la vue Liste ouvre le même détail ;
- un double-clic sur une journée vide prépare une nouvelle échéance à cette date ;
- **Planifier une échéance** ouvre un formulaire vide.

## 6. Générer un rapport

Dans **Rapports**, l'utilisateur sélectionne un modèle dans le catalogue, configure le périmètre et choisit les sections à inclure. Il sélectionne ensuite le format :

- **PDF** pour un document officiel mis en page ;
- **Excel** pour les tableaux et analyses détaillés ;
- **CSV** pour les données brutes interopérables.

Le bouton **Aperçu** permet de contrôler le titre, la période et les principaux indicateurs. **Générer le rapport** lance ensuite la production du fichier. L'utilisateur retrouve le résultat dans l'historique des générations selon ses autorisations.

Les exports affichés dans la maquette sont simulés jusqu'au raccordement du moteur de reporting FastAPI.

## 7. Administrer les utilisateurs

Dans **Administration**, un administrateur peut rechercher les comptes, consulter leur statut et ouvrir leur fiche détaillée. **Nouvel utilisateur** permet de renseigner l'identité, le rôle, la région d'affectation et les autorisations complémentaires avant l'envoi de l'invitation.

Les opérations sensibles — changement de rôle, blocage, réinitialisation du mot de passe et modification des permissions — devront être enregistrées dans le journal d'audit. Un administrateur ne doit jamais connaître le mot de passe d'un utilisateur : la réinitialisation doit transmettre un lien temporaire sécurisé.

## 8. Gérer les référentiels

La page **Référentiels** contient les valeurs normalisées proposées dans les formulaires et les filtres. L'administrateur sélectionne une catégorie, recherche un code puis crée, modifie ou désactive un élément.

Avant toute modification d'une valeur déjà utilisée, il doit consulter ses dépendances. La désactivation est préférable à la suppression afin de conserver l'interprétation des anciens dossiers. Toute modification sensible devra être versionnée et inscrite au journal d'audit.

## 9. Configurer les règles et la codification

La page **Règles & codification** permet de préparer une nouvelle version des seuils, pondérations, délais et formats d'identifiants. L'administrateur enregistre d'abord un brouillon, utilise le simulateur, puis renseigne le motif et la référence d'autorisation avant publication.

Une version publiée doit être immuable. Chaque contrôle, score ou code doit conserver la version ayant servi à son calcul afin que les résultats historiques restent reproductibles.

## 10. Audit, connexion et profil

### Création des utilisateurs et attribution des rôles

Dans **Administration > Utilisateurs et accès**, l'administrateur clique sur **Nouvel utilisateur**, renseigne prénom, nom, adresse professionnelle, fonction, téléphone, rôle principal, région et permissions complémentaires, puis choisit d'envoyer l'invitation. L'utilisateur reçoit un lien à durée limitée, définit son mot de passe et active son compte. L'administrateur peut ensuite modifier le rôle, désactiver ou bloquer le compte et demander une réinitialisation du mot de passe. Cette interface existe déjà dans la maquette ; FastAPI devra créer réellement le compte, le jeton d'invitation et l'envoi email.

Dans **Règles & codification > Alertes et emails**, l'administrateur configure séparément les alertes d'audit, d'expiration et d'échéance. Il sélectionne les utilisateurs enregistrés qui recevront chaque type de message et peut ajouter des adresses supplémentaires. Les comptes inactifs ou bloqués ne doivent pas recevoir les notifications.

Le **Journal d'audit** permet aux profils autorisés de rechercher une opération et d'afficher son contexte ainsi que les valeurs avant/après. Il est strictement en lecture seule.

La page **Connexion** demande l'adresse professionnelle et le mot de passe. Après plusieurs échecs, le compte pourra être temporairement bloqué. **Mot de passe oublié** transmet un lien temporaire sans confirmer publiquement l'existence du compte.

Le menu utilisateur ouvre **Profil et préférences** : coordonnées, mot de passe, MFA, notifications et sessions actives. Le rôle et les autorisations restent administrés dans la page Utilisateurs.

Dans **Sécurité**, l'utilisateur peut activer le verrouillage automatique, créer un code privé d'au moins cinq caractères et choisir 5, 10, 15 ou 30 minutes d'inactivité. **Tester** verrouille immédiatement l'écran. Le code reprend la session ; cinq erreurs conduisent à la déconnexion. Dans la maquette le mécanisme est local ; FastAPI devra le contrôler et conserver uniquement une empreinte du code.

### Barre supérieure

- la **cloche** ouvre les dernières notifications et permet de les marquer comme lues ;
- chaque notification conduit au module concerné ;
- **Voir toutes les alertes** ouvre le centre des alertes ;
- le menu portant le nom de l'utilisateur donne accès au profil, à la sécurité, aux préférences, à l'activité et à la déconnexion ;
- le switch **Clair/Sombre** de la barre supérieure change immédiatement l'apparence de toute l'application et conserve le choix sur l'appareil ;
- un clic à l'extérieur ou la touche `Échap` ferme les menus.

## 11. Évolutions validées à intégrer au guide

Les fonctionnalités ci-dessous sont validées fonctionnellement mais ne sont pas toutes encore développées. Le guide devra être complété au moment de leur livraison, sans les présenter prématurément comme disponibles.

### Certifications et renouvellement

L'utilisateur devra voir les contrôles de dates, la présence des justificatifs, les doublons potentiels, le statut **À vérifier**, la procédure officielle de renouvellement et l'historique des versions. Une certification sans expiration ne sera autorisée que si son référentiel le prévoit.

### Alertes

Les niveaux de référence sont 180 jours, 90 jours, 30 jours et expiration. L'alerte critique reste ouverte jusqu'à régularisation ou clôture. Le guide expliquera les relances, preuves, réponses, responsables et notifications.

### Entreprises et organismes

Une entreprise sans RCCM pourra être enregistrée **En attente de régularisation**. Les statuts actif, à risque et non conforme seront calculés. Les organismes non accrédités resteront enregistrables, mais leurs certificats seront signalés **À vérifier**. Les suspensions d'accréditation déclencheront une vérification.

### Trois résultats à ne pas confondre

Le guide présentera séparément :

- la classification globale de l'entreprise : Conforme, À surveiller ou Non conforme ;
- l'INFC d'une certification sur 100 ;
- le classement SNCC : classe, statut administratif et niveau de risque.

### Parcours d'un dossier

Le parcours officiel est :

**Brouillon → Soumise → Vérification → Contrôle → Validation définitive → Intégration BNEC → Classification/INFC → SNCC → Veille**

Chaque étape disposera de sa file, de ses actions autorisées, de ses motifs de retour et de son historique.

### Sécurité, exports et archives

Le guide expliquera la désactivation après 180 jours d'inactivité, le préavis de 30 jours, le verrouillage après cinq échecs, les permissions d'export, le motif obligatoire, l'archivage sans suppression définitive et la consultation restreinte des versions antérieures.

### Administration

Les administrateurs habilités géreront les pondérations, seuils, alertes, délais, référentiels, permissions et codifications sans modifier le code. Ils superviseront aussi les sauvegardes et tests de restauration.

### Qualité et publication

Une revue annuelle produira anomalies et plans d'action. Toute publication suivra le circuit **Brouillon → Soumis → Approuvé → Publié → Retiré** et les données publiques resteront agrégées.

### Documentation technique associée

La documentation technique devra maintenir la matrice **règle RM → écran → permission → table → API → audit → test**, ainsi que le dictionnaire de données, les statuts et la matrice des permissions.

## 12. Pages à documenter

- Tableau de bord
- Alertes
- Échéances
- Entreprises : liste, dossier et formulaire
- Certifications : liste, dossier et formulaire
- Organismes : liste, dossier et formulaire
- Collectes : missions et formulaire numérique
- Validations et affectation des dossiers
- Vérifications documentaires
- Grille de contrôle
- Intégrations BNEC
- Scoring
- INFC
- Classement SNCC
- Cellule de Veille des Certifications
- Décisions et plans d'action
- Demandes de mise à jour
- Échanges avec les organismes certificateurs
- Gestion documentaire
- Incidents et amélioration continue
- Qualité des données
- Sauvegardes et restaurations
- Publications
- Tableaux de bord tactique, stratégique et annuel
- Baromètre et tableau de bord public
- Rapports
- Administration
- Authentification et profil

## 13. Éléments à ajouter avant livraison

- captures d'écran validées ;
- prérequis et procédure de connexion ;
- détail de chaque bouton et message d'erreur ;
- matrice complète des rôles et autorisations ;
- procédures d'export Excel, PDF et CSV ;
- gestion des notifications et des échéances ;
- questions fréquentes et résolution des incidents.
