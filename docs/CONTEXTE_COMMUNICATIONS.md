# Contexte partagé des communications

## Objectif du fichier

Ce document centralise les informations utiles à la rédaction des courriels et des réponses concernant le projet. Il doit être consulté avant toute rédaction et actualisé lorsque de nouvelles informations importantes apparaissent.

## Préférences rédactionnelles

- Langue principale : français.
- Ton attendu : professionnel, courtois, clair et naturel.
- Préserver l'intention initiale du message tout en corrigeant l'orthographe, la grammaire et la formulation.
- Éviter les formulations inutilement longues ou trop administratives.
- Proposer un objet pertinent lorsque le texte est destiné à être envoyé par courriel.
- Employer des formules d'appel et de politesse adaptées aux destinataires.
- Ne pas inventer d'informations absentes du contexte fourni.
- Pour les énumérations, utiliser un tiret (`-`) comme marqueur et non un point ou une puce ronde.
- Ne pas ajouter de lignes ou de séparations horizontales décoratives dans les documents.
- Les zones de texte doivent rester sans contour visible afin de ne pas créer de traits horizontaux entre les blocs de texte.

## Projet concerné

- Nom de travail du système : **HAUQE Certif**.
- Bénéficiaire : **Haute Autorité de la Qualité et de l'Environnement (HAUQE)**.
- Contexte de la mission : GIZ / ProComp, avec appui technique de GFA Consulting Group.
- Développement d'une base nationale de gestion et de suivi des certifications à partir d'une fiche unique de collecte.
- Les données concernent environ 100 entreprises certifiées ainsi que les organismes certificateurs au Togo.
- Le calendrier de développement est court.
- Il est nécessaire de prévoir suffisamment de temps pour vérifier et intégrer dans la base les données collectées sur le terrain.
- Document de référence mentionné : fiche unique de collecte transmise par Monsieur NYANUTSE.
- Période de collecte terrain communiquée : **du 27 juillet au 7 août 2026**.
- Objectif communiqué au développeur : disposer d'un système opérationnel avant le démarrage de la collecte du 27 juillet.

Le développeur intervient principalement en aval de la collecte : il prépare la structure, reçoit les données collectées par les équipes terrain, les contrôle, les harmonise et les intègre. Il ne faut pas lui attribuer automatiquement les obligations terrain du chef d'équipe prévues dans les TDR.

## Interlocuteurs connus

### Monsieur NYANUTSE

- A transmis la fiche unique de collecte servant de référence pour les champs de la base de données.
- Fonction : à préciser.

### Monsieur Achille

- Interlocuteur associé à la validation des règles métier et à l'examen de la proposition concernant la fiche de collecte.
- A transmis ou relayé un annuaire/document de référence sur les certifications existantes au Togo.
- L'annuaire doit être considéré comme un document de contexte, et non nécessairement comme une source à importer telle quelle.
- Identité complète et fonction : à préciser.

### Madame DA-AFI

- Destinataire des échanges relatifs au démarrage du développement de la base.
- Devait communiquer la liste des entreprises à visiter.
- Également concernée par la validation du document des règles métier.
- Fonction : à préciser.

### Monsieur Roland

- Prénom de l'expéditeur/développeur mentionné dans les échanges antérieurs.
- Nom complet, fonction exacte et signature professionnelle : à préciser.

## Échanges et décisions

### Démarrage du développement de la base

- Proposition : commencer la conception de la base en s'appuyant sur les champs de la fiche unique de collecte.
- Motif : respecter les échéances et conserver assez de temps pour vérifier puis intégrer les données recueillies sur le terrain.
- Statut : message préparé ; réponse ou validation des destinataires à renseigner.

### Courriel 1 — Appréciation de la fiche HAUQE/FUCCS/01

- **Objet de l'échange :** transmettre une appréciation technique de la fiche unique de collecte.
- **Proposition principale :** scinder la fiche en deux niveaux :
  1. les champs primordiaux nécessaires à l'identification et à la première saisie ;
  2. les informations destinées au contrôle approfondi et à la vérification.
- **Motif :** rendre la collecte terrain plus simple tout en conservant un contrôle détaillé dans le système.
- **Destinataire principal mentionné :** Monsieur Achille ; autres destinataires à confirmer.
- **Statut connu :** courriel préparé ; réaction de Monsieur Achille attendue.
- **Traçabilité :** le texte intégral du courriel n'a pas été retrouvé dans les fichiers consultés. Ne pas reconstituer ses phrases comme s'il s'agissait du message original.

### Courriel 2 — Transmission des règles métier

- **Objet de l'échange :** envoyer le document des règles métier pour examen et validation.
- **Destinataires mentionnés :** Monsieur Achille et Madame DA-AFI.
- **Finalité :** obtenir une validation formelle avant de figer les workflows, les contrôles, la codification et la structure de la base.
- **Statut connu :** courriel préparé ; validation attendue.
- **Traçabilité :** le texte intégral du courriel n'a pas été retrouvé dans les fichiers consultés. Ne pas inventer son objet exact, son contenu ni sa date d'envoi.

### Informations attendues à la suite de ces courriels

Au dernier état connu, les retours suivants étaient attendus :

1. validation des règles métier ;
2. liste des entreprises à visiter, à communiquer par Madame DA-AFI ;
3. réaction de Monsieur Achille à la proposition de scinder la fiche de collecte.

Ces trois éléments restent marqués **à confirmer** tant qu'une réponse datée ou un document validé n'est pas enregistré.

### Lecture de l'annuaire/document des certifications existantes

L'annuaire transmis par Monsieur Achille a été interprété comme une référence destinée à comprendre les entreprises, produits, normes et certifications susceptibles d'être rencontrés. Les conséquences relevées pour le système sont les suivantes :

- les certifications ne se limitent pas aux normes ISO ;
- prévoir notamment les références COTAG et les normes citées dans l'échange : `ARS 464`, `ARS 466`, `ECOSTAND` et `DOC-CERT` ;
- la fiche HAUQE/FUCCS/01 mentionne notamment HACCP, ISO 22000, FSSC 22000, BIO, BRCGS et ISO 9001, mais les références COTAG n'y apparaissaient pas dans l'analyse antérieure ;
- ce décalage doit être signalé et validé avant de figer le référentiel des normes ;
- le système de codification doit pouvoir gérer des références de type `TGN/COTAG/XXX/DG/2025` ;
- les produits concernés sont variés : riz, manioc, jus, boissons alcooliques, volaille, fonio, entre autres ; le référentiel produit ne doit donc pas être limité à une liste étroite ou codée en dur.

### Distinction entre les TDR du chef d'équipe et le travail du développeur

Les TDR décrivent une mission comprenant réunion de lancement, collecte terrain, entretiens, vérification physique des justificatifs, harmonisation et rapport. Une partie de ces obligations relève du chef d'équipe et des agents de terrain.

Pour le développeur de la base, les attentes directement retenues sont :

- préparer le modèle de données avant la réception des résultats terrain ;
- structurer les informations des entreprises, certifications et organismes certificateurs ;
- faciliter la vérification, la correction et l'harmonisation des données ;
- constituer une base exploitable pour le futur système national de gestion des certifications ;
- éviter d'attendre la fin du terrain pour concevoir la structure, compte tenu des délais très courts d'intégration.

Les TDR ne fixaient pas précisément le moteur de base, l'architecture technique ni tous les champs. Ces éléments doivent provenir de la fiche validée et des décisions de cadrage.

## Décisions techniques et fonctionnelles liées aux communications

- Frontend retenu : HTML, CSS, Bootstrap et JavaScript.
- Backend prévu : Python avec FastAPI.
- Base prévue : PostgreSQL.
- Le frontend est actuellement une maquette fonctionnelle alimentée par des données simulées.
- La conception définitive de la base attend la validation des champs de collecte et des règles métier.
- La fiche communiquée par Monsieur NYANUTSE reste la référence principale pour rapprocher les écrans et le futur dictionnaire de données.

## Méthode d'enregistrement des prochaines communications

Pour chaque nouveau courriel, message, réunion ou appel, ajouter une entrée comprenant :

- date et heure ;
- canal : courriel, WhatsApp, téléphone, réunion ou autre ;
- expéditeur et destinataires ;
- objet ou sujet ;
- résumé fidèle ;
- décisions prises ;
- actions attendues, responsable et échéance ;
- pièces jointes ou fichiers concernés ;
- statut : brouillon, envoyé, reçu, validé, refusé ou en attente ;
- lien ou emplacement du texte original lorsque disponible.

Ne jamais transformer une proposition en décision validée sans preuve du retour correspondant.

## Informations à compléter

- Nom officiel du projet.
- Identité et fonction exactes des interlocuteurs.
- Nom et signature professionnelle de l'expéditeur.
- Confirmation du calendrier terrain du 27 juillet au 7 août 2026.
- Date d'envoi et texte original des deux courriels préparés.
- Décisions ou validations reçues en réponse.
- Version approuvée de la fiche HAUQE/FUCCS/01.
- Version approuvée des règles métier.
- Liste officielle des entreprises à visiter.
- Autres destinataires réguliers.

## Historique des mises à jour

- 17 juillet 2026 : création du fichier à partir des informations disponibles dans la discussion consacrée à la rédaction des courriels.
- 17 juillet 2026 : ajout du contexte HAUQE/GIZ/GFA, des deux courriels préparés, des retours attendus, du calendrier terrain communiqué, des observations COTAG et de la distinction entre les obligations terrain et le rôle du développeur.
