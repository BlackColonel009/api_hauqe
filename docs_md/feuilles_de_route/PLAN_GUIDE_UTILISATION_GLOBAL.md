# Plan de développement - Guide global d'utilisation SNGSC / HAUQE

**Statut :** guide opérationnel V2 illustré et détaillé pour la formation ; recette métier finale à poursuivre
**Dernière mise à jour :** 21 septembre 2026
**Livrable cible :** document Word `.docx` modifiable et prêt pour impression

## Avancement documentaire - 21 septembre 2026

- une version rédigée du guide global a été produite dans
  `docs_md/guide_global_utilisation_SNGSC_HAUQE_version_redigee.docx` ;
- elle couvre les parcours fonctionnels disponibles ou préparés dans le code
  local, sans y intégrer de capture d'écran ;
- des cadres de figures sont présents pour l'insertion ultérieure des captures
  nettoyées par la HAUQE.
- un guide opérationnel enrichi est disponible dans
  `output/docx/Guide_global_utilisation_SNGSC_HAUQE_v2.docx` ; il contient
  des procédures pas à pas, les rôles concernés, les prérequis, les résultats
  attendus, les points d'attention et un cadre de figure par chapitre ;
- les captures ajoutées par l'équipe sont intégrées au guide ;
- chaque chapitre comporte désormais une introduction fonctionnelle et les
  légendes décrivent les actions visibles dans les captures ;
- la gestion des campagnes, le classement SNCC, l'exemple fictif de collecte
  et la matrice RACI des rôles ont été ajoutés pour la formation.

## 1. Objectif

Produire un manuel professionnel permettant aux agents habilités de comprendre
et d'utiliser le SNGSC, sans exposer les secrets, l'infrastructure, les mots
de passe ou les détails techniques sensibles.

Le document doit rester simple, illustrable et adapté à une impression
physique.

## 2. Décisions de format

- format A4 portrait ; pages paysage seulement pour les tableaux trop larges ;
- page de garde institutionnelle HAUQE ;
- en-tête avec le nom du chapitre ; pied de page avec version, confidentialité
  et pagination ;
- table des matières automatique, liste des figures et liste des tableaux ;
- styles Word cohérents et entièrement modifiables ;
- charte verte de l'application, avec orange pour les points d'attention et
  rouge pour les avertissements ;
- aucun screenshot intégré par l'assistant : des cadres réservés seront créés
  afin que la HAUQE insère ses propres captures ;
- taille visée après insertion des captures : environ 100 à 150 pages.

## 3. Structure retenue

1. Page de garde et fiche documentaire ;
2. Avertissement, diffusion, historique des versions et lecture du guide ;
3. Table des matières, liste des figures, liste des tableaux et glossaire ;
4. Présentation du SNGSC et parcours global d'une certification ;
5. Connexion, sécurité, MFA, mot de passe oublié et verrouillage de session ;
6. Profil, photo, préférences, notifications et actualisation automatique ;
7. Tableau de bord, alertes et échéances ;
8. Registre national : entreprises, organismes, zones et certifications ;
9. Collecte : campagne, mission, déclarant, offres, certifications, preuves
   et soumission ;
10. Vérification documentaire et contrôle FUCCS ;
11. Validation N1/N2 et intégration BNEC ;
12. Scoring, INFC et classement SNCC ;
13. Veille, relances, décisions, actions et communication ;
14. Tableaux tactique, stratégique, annuel, national et public ;
15. Administration : utilisateurs, référentiels, règles, documents,
    organismes et publications ;
16. Audit, qualité des données, mises à jour BNEC, sauvegarde et restauration ;
17. Rapports et exportations ;
18. Assistance, erreurs fréquentes et annexes.

## 4. Gabarit de chaque module

Chaque page fonctionnelle doit employer le même ordre :

1. objectif de la page ;
2. utilisateurs ou rôles concernés ;
3. prérequis ;
4. présentation de l'interface ;
5. cadre de capture d'écran ;
6. légende numérotée ;
7. procédure pas à pas ;
8. résultat attendu ;
9. points d'attention et erreurs fréquentes ;
10. liens avec les autres modules.

## 5. Convention pour les captures

Chaque cadre comprendra le titre « Figure X - Capture à insérer » et la note :

> Masquer les données nominatives, identifiants, adresses électroniques et
> informations sensibles avant insertion.

Une légende prête à compléter sera placée sous chaque cadre : titre, filtres,
bouton principal, tableau ou cartes, actions, pagination et notifications.

## 6. Phases de production

### Phase 1 - Squelette Word — réalisée

Créer le `.docx` avec la page de garde, les styles, les en-têtes, les pieds de
page, la table des matières, tous les chapitres, les cadres d'images et les
gabarits de procédure.

### Phase 2 - Rédaction fonctionnelle — réalisée pour la version V2

Rédiger les parties par lots cohérents, en commençant par la prise en main,
le profil et le tableau de bord.

### Phase 3 - Insertion des captures par la HAUQE — réalisée

Les captures ont été insérées dans la version illustrée et les légendes ont
été rapprochées des écrans correspondants.

### Phase 4 - Contrôle et livraison — en cours

Vérifier les renvois, la table des matières, les rôles, l'impression et le
rendu de chaque page ; livrer le Word modifiable puis, si souhaité, le PDF
officiel.

## 7. Prochaine action exacte

Ouvrir le guide détaillé dans Word, mettre à jour tous les champs avec
`Ctrl+A`, puis `F9`, et relire les procédures avec les agents pendant la
formation. Corriger ensuite les éventuels écarts constatés lors de la recette
métier avant la livraison définitive.

## 8. Mise à jour ciblée - Guide SNCC (21/09/2026)

Le guide PDF accessible depuis l'écran **Classement SNCC** est enrichi afin de
lever les ambiguïtés de vocabulaire. Il présente désormais :

- les définitions opérationnelles des classes A+ à D ;
- les statuts administratifs VA, RE, SU, RT, EX et VE ;
- les niveaux de risque R1 à R5 ;
- les familles d'anomalies, exemples de constats et réponses attendues ;
- la distinction impérative entre classe, statut administratif et risque.

Le fichier produit est `output/pdf/guide-sncc-hauqe.pdf`, puis recopié dans
`app/static/docs/guide-sncc-hauqe.pdf` pour être consultable dans l'application.

## 9. Mise à jour ciblée - Parcours de traitement d'un dossier (21/09/2026)

Ajouter au guide une capture du bloc **Parcours de traitement** visible dans
la fiche de collecte puis dans les écrans Vérification, Contrôle FUCCS,
Validation et Intégration BNEC. Le bloc présente les six étapes réelles :
collecte, vérification documentaire, contrôle FUCCS, validation N1,
validation N2 et intégration BNEC. Il met en évidence l'étape en cours, la
prochaine action, les blocages éventuels et les étapes restantes, sans exposer
d'identifiant technique.
