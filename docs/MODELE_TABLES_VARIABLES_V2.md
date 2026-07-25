# Modèle rationalisé des tables et variables — HAUQE Certif

**Version :** 0.2  
**Statut :** proposition de travail à valider  
**Cible :** FastAPI + PostgreSQL  
**Convention :** `PK` = clé primaire, `FK` = clé étrangère, `UQ` = valeur unique.

Les champs transversaux `created_at`, `updated_at`, `created_by` et `is_active` seront ajoutés aux tables qui en ont besoin lors du passage au MPD.

## 1. Sécurité et utilisateurs

### 1. utilisateurs

- `id` — PK
- `email` — UQ
- `mot_de_passe_hash`
- `nom`
- `prenoms`
- `telephone`
- `fonction`
- `region_affectation_id` — FK vers `zones_administratives.id`, facultatif
- `statut`
- `mfa_active`
- `derniere_connexion_at`

### 2. roles

- `id` — PK
- `code` — UQ
- `libelle`
- `description`
- `niveau`
- `statut`

### 3. permissions

- `id` — PK
- `code` — UQ
- `domaine`
- `action`
- `description`

### 4. utilisateur_role

- `id` — PK
- `utilisateur_id` — FK vers `utilisateurs.id`
- `role_id` — FK vers `roles.id`
- `date_debut`
- `date_fin`
- `attribue_par_id` — FK vers `utilisateurs.id`
- `motif`
- `statut`

### 5. role_permission

- `id` — PK
- `role_id` — FK vers `roles.id`
- `permission_id` — FK vers `permissions.id`

### 6. sessions_utilisateur

- `id` — PK
- `utilisateur_id` — FK vers `utilisateurs.id`
- `jeton_hash`
- `adresse_ip`
- `user_agent`
- `debut_at`
- `derniere_activite_at`
- `expiration_at`
- `revoquee_at`

## 2. Référentiels

### 7. zones_administratives

- `id` — PK
- `parent_id` — FK récursive vers `zones_administratives.id`, facultatif
- `type_zone` — région, préfecture, commune ou localité
- `code`
- `nom`
- `latitude`
- `longitude`
- `statut`

### 8. referentiels

- `id` — PK
- `code` — UQ
- `libelle`
- `description`
- `type_valeur`
- `statut`

### 9. valeurs_referentiel

- `id` — PK
- `referentiel_id` — FK vers `referentiels.id`
- `parent_id` — FK récursive facultative
- `code`
- `libelle`
- `description`
- `ordre_affichage`
- `date_debut_validite`
- `date_fin_validite`
- `statut`

### 10. normes

- `id` — PK
- `code`
- `nom`
- `version`
- `autorite_emettrice`
- `domaine`
- `portee`
- `date_debut_application`
- `date_fin_application`
- `date_expiration`
- `statut`

## 3. Entreprises

### 11. entreprises

- `id` — PK
- `identifiant_national` — UQ
- `raison_sociale`
- `nom_commercial`
- `forme_juridique`
- `rccm`
- `nif`
- `ifu`
- `date_creation`
- `nationalite`
- `capital_social`
- `effectif`
- `chiffre_affaires`
- `email_principal`
- `telephone_principal`
- `site_web`
- `adresse_siege`
- `zone_siege_id` — FK vers `zones_administratives.id`
- `activite_principale`
- `secteurs_secondaires` — liste contrôlée
- `statut`
- `niveau_risque`
- `source_donnee`
- `date_derniere_verification`

### 12. contacts_entreprise

- `id` — PK
- `entreprise_id` — FK vers `entreprises.id`
- `nom`
- `prenoms`
- `fonction`
- `telephone`
- `email`
- `type_contact`
- `contact_principal`
- `statut`

### 13. sites_entreprise

- `id` — PK
- `entreprise_id` — FK vers `entreprises.id`
- `nom`
- `type_site`
- `adresse`
- `zone_id` — FK vers `zones_administratives.id`
- `latitude`
- `longitude`
- `date_ouverture`
- `effectif`
- `statut`

### 14. offres_entreprise

- `id` — PK
- `entreprise_id` — FK vers `entreprises.id`
- `type_offre` — produit ou service
- `nom`
- `description`
- `categorie`
- `volume_annuel`
- `unite`
- `capacite_production`
- `marches_cibles`
- `destinations`
- `statut`

### 15. candidats_doublon

- `id` — PK
- `entreprise_source_id` — FK vers `entreprises.id`
- `entreprise_cible_id` — FK vers `entreprises.id`
- `criteres_concordants`
- `score_similarite`
- `statut_examen`
- `decision`
- `motif_decision`
- `examine_par_id` — FK vers `utilisateurs.id`
- `examine_at`

## 4. Organismes et certifications

### 16. organismes

- `id` — PK
- `identifiant_national`
- `nom_officiel`
- `sigle`
- `type_organisme`
- `pays`
- `numero_enregistrement`
- `email`
- `telephone`
- `adresse`
- `zone_id` — FK vers `zones_administratives.id`, facultatif
- `site_web`
- `statut`
- `date_derniere_verification`

### 17. accreditations

- `id` — PK
- `organisme_id` — FK vers `organismes.id`
- `numero`
- `accrediteur`
- `domaine_technique`
- `perimetre`
- `date_delivrance`
- `date_expiration`
- `statut`
- `reference_officielle`
- `decision_hauqe`
- `date_decision`

### 18. certifications

- `id` — PK
- `identifiant_national` — UQ
- `entreprise_id` — FK vers `entreprises.id`
- `organisme_id` — FK vers `organismes.id`
- `accreditation_id` — FK vers `accreditations.id`, facultatif
- `norme_id` — FK vers `normes.id`
- `numero_certificat`
- `portee`
- `date_obtention`
- `date_effet`
- `date_expiration`
- `statut`
- `motif_statut`
- `classification`
- `authenticite_verifiee`
- `certification_strategique`
- `source_donnee`

### 19. couvertures_certification

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `type_couverture` — produit, service, site ou activité
- `offre_entreprise_id` — FK vers `offres_entreprise.id`, facultatif
- `site_entreprise_id` — FK vers `sites_entreprise.id`, facultatif
- `libelle_couverture`
- `details`
- `statut`

### 20. audits_certification

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `type_audit`
- `date_prevue`
- `date_realisee`
- `auditeur`
- `resultat`
- `prochain_audit_at`
- `observations`
- `statut`

### 21. evenements_certification

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `type_evenement`
- `ancien_statut`
- `nouveau_statut`
- `date_evenement`
- `motif`
- `source`
- `acteur_id` — FK vers `utilisateurs.id`, facultatif

### 22. renouvellements_certification

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `date_ouverture`
- `date_limite`
- `date_decision`
- `decision`
- `resultat`
- `justification`
- `preuves`
- `statut`

### 23. documents

- `id` — PK
- `type_document`
- `nom_original`
- `nom_stockage`
- `chemin_stockage`
- `format`
- `taille_octets`
- `checksum`
- `version`
- `ressource_type`
- `ressource_id`
- `confidentialite`
- `source`
- `date_document`
- `depose_par_id` — FK vers `utilisateurs.id`, facultatif
- `date_depot`
- `statut_verification`
- `statut`

## 5. Collecte

### 24. campagnes

- `id` — PK
- `code` — UQ
- `nom`
- `objet`
- `objectif`
- `date_debut`
- `date_fin`
- `responsable_id` — FK vers `utilisateurs.id`
- `statut`

### 25. missions_collecte

- `id` — PK
- `campagne_id` — FK vers `campagnes.id`
- `code`
- `objet`
- `zone_id` — FK vers `zones_administratives.id`
- `date_debut_prevue`
- `date_fin_prevue`
- `date_debut_reelle`
- `date_fin_reelle`
- `priorite`
- `progression`
- `statut`

### 26. affectations_mission

- `id` — PK
- `mission_id` — FK vers `missions_collecte.id`
- `utilisateur_id` — FK vers `utilisateurs.id`
- `role_mission`
- `date_debut`
- `date_fin`
- `attribue_par_id` — FK vers `utilisateurs.id`
- `motif`
- `statut`

### 27. fiches_collecte

- `id` — PK
- `mission_id` — FK vers `missions_collecte.id`
- `entreprise_id` — FK vers `entreprises.id`, facultatif
- `version_formulaire`
- `numero_revision`
- `statut`
- `taux_completude`
- `consentement_obtenu`
- `nom_declarant`
- `fonction_declarant`
- `telephone_declarant`
- `email_declarant`
- `signature_declarant`
- `observations`
- `collecte_par_id` — FK vers `utilisateurs.id`
- `collecte_at`
- `soumise_at`

### 28. offres_declarees

- `id` — PK
- `fiche_collecte_id` — FK vers `fiches_collecte.id`
- `type_offre`
- `nom`
- `description`
- `categorie`
- `volume`
- `unite`
- `capacite`
- `marches_vises`
- `statut`

### 29. certifications_declarees

- `id` — PK
- `fiche_collecte_id` — FK vers `fiches_collecte.id`
- `nom_certification`
- `numero`
- `organisme_declare`
- `norme_declaree`
- `portee`
- `date_obtention`
- `date_expiration`
- `copie_disponible`
- `certification_officielle_id` — FK vers `certifications.id`, facultatif
- `score_rapprochement`
- `statut_rapprochement`

### 30. evenements_collecte

- `id` — PK
- `fiche_collecte_id` — FK vers `fiches_collecte.id`
- `type_evenement`
- `ancien_statut`
- `nouveau_statut`
- `commentaire`
- `acteur_id` — FK vers `utilisateurs.id`
- `date_evenement`

## 6. Vérification

### 31. dossiers_verification

- `id` — PK
- `fiche_collecte_id` — FK vers `fiches_collecte.id`
- `date_ouverture`
- `date_fin`
- `statut`
- `avis`
- `synthese`
- `niveau_risque`
- `priorite`

### 32. affectations_verification

- `id` — PK
- `dossier_verification_id` — FK vers `dossiers_verification.id`
- `verificateur_id` — FK vers `utilisateurs.id`
- `date_debut`
- `date_fin`
- `date_echeance`
- `motif`
- `statut`

### 33. points_verification

- `id` — PK
- `dossier_verification_id` — FK vers `dossiers_verification.id`
- `code`
- `libelle`
- `categorie`
- `resultat`
- `observation`
- `date_verification`
- `preuve_document_id` — FK vers `documents.id`, facultatif
- `verifie_par_id` — FK vers `utilisateurs.id`

### 34. anomalies_verification

- `id` — PK
- `dossier_verification_id` — FK vers `dossiers_verification.id`
- `point_verification_id` — FK vers `points_verification.id`, facultatif
- `categorie`
- `gravite`
- `description`
- `statut`
- `resolution`
- `date_resolution`
- `escalade`

### 35. confirmations_externes

- `id` — PK
- `dossier_verification_id` — FK vers `dossiers_verification.id`
- `organisme_id` — FK vers `organismes.id`, facultatif
- `canal`
- `destinataire`
- `objet`
- `date_envoi`
- `date_echeance`
- `date_reponse`
- `contenu_reponse`
- `resultat`
- `document_id` — FK vers `documents.id`, facultatif
- `statut`

## 7. Contrôle FUCCS et intégration

### 36. grilles_fuccs

- `id` — PK
- `code`
- `libelle`
- `version`
- `date_effet`
- `date_fin`
- `reference_approbation`
- `statut_publication`

### 37. rubriques_fuccs

- `id` — PK
- `grille_fuccs_id` — FK vers `grilles_fuccs.id`
- `code`
- `libelle`
- `description`
- `ordre_affichage`

### 38. criteres_fuccs

- `id` — PK
- `rubrique_fuccs_id` — FK vers `rubriques_fuccs.id`
- `code`
- `libelle`
- `description`
- `score_maximal`
- `poids`
- `ordre_affichage`
- `commentaire_obligatoire`
- `preuve_obligatoire`

### 39. controles_fuccs

- `id` — PK
- `dossier_verification_id` — FK vers `dossiers_verification.id`
- `grille_fuccs_id` — FK vers `grilles_fuccs.id`
- `controleur_id` — FK vers `utilisateurs.id`
- `date_debut`
- `date_fin`
- `score_brut`
- `score_maximal`
- `taux`
- `synthese`
- `statut`

### 40. notes_criteres

- `id` — PK
- `controle_fuccs_id` — FK vers `controles_fuccs.id`
- `critere_fuccs_id` — FK vers `criteres_fuccs.id`
- `score`
- `commentaire`
- `preuve_document_id` — FK vers `documents.id`, facultatif
- `note_par_id` — FK vers `utilisateurs.id`

### 41. constats_controle

- `id` — PK
- `controle_fuccs_id` — FK vers `controles_fuccs.id`
- `type_constat`
- `gravite`
- `titre`
- `description`
- `statut`

### 42. validations

- `id` — PK
- `fiche_collecte_id` — FK vers `fiches_collecte.id`
- `controle_fuccs_id` — FK vers `controles_fuccs.id`, facultatif
- `niveau_validation`
- `validateur_id` — FK vers `utilisateurs.id`
- `decision`
- `date_validation`
- `reserves`
- `justification`
- `statut`

### 43. corrections

- `id` — PK
- `validation_id` — FK vers `validations.id`
- `motif`
- `instructions`
- `date_demande`
- `date_echeance`
- `date_resoumission`
- `reponse`
- `statut`

### 44. integrations_bnec

- `id` — PK
- `validation_id` — FK vers `validations.id`
- `administrateur_id` — FK vers `utilisateurs.id`
- `date_debut`
- `date_fin`
- `statut`
- `precontrole`
- `postcontrole`
- `sauvegarde_reference`
- `resume`

### 45. elements_integration

- `id` — PK
- `integration_bnec_id` — FK vers `integrations_bnec.id`
- `type_objet`
- `ressource_source_id`
- `ressource_cible_id`
- `revision_source`
- `action`
- `code_genere`
- `statut`
- `message_erreur`

## 8. Scoring et classification

### 46. modeles_scoring

- `id` — PK
- `code`
- `libelle`
- `version`
- `objet_evalue`
- `description`
- `date_debut_validite`
- `date_fin_validite`
- `regle_calcul`
- `reference_approbation`
- `statut`

### 47. ponderations_scoring

- `id` — PK
- `modele_scoring_id` — FK vers `modeles_scoring.id`
- `domaine`
- `valeur`
- `periode_debut`
- `periode_fin`
- `statut`

### 48. classifications_entreprise

- `id` — PK
- `entreprise_id` — FK vers `entreprises.id`
- `modele_scoring_id` — FK vers `modeles_scoring.id`
- `score`
- `classe`
- `date_calcul`
- `date_validation`
- `sources`
- `valide_par_id` — FK vers `utilisateurs.id`
- `statut`

### 49. resultats_infc

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `modele_scoring_id` — FK vers `modeles_scoring.id`
- `score_global`
- `niveau`
- `scores_domaines`
- `date_calcul`
- `date_validation`
- `sources`
- `statut`

### 50. classements_sncc

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `classe`
- `statut_administratif`
- `niveau_risque`
- `justification`
- `date_effet`
- `date_fin`
- `valide_par_id` — FK vers `utilisateurs.id`
- `statut`

## 9. Échéances, alertes et veille

### 51. echeances

- `id` — PK
- `ressource_type`
- `ressource_id`
- `type_echeance`
- `titre`
- `description`
- `date_echeance`
- `responsable_id` — FK vers `utilisateurs.id`, facultatif
- `priorite`
- `statut`

### 52. alertes

- `id` — PK
- `echeance_id` — FK vers `echeances.id`, facultatif
- `type_alerte`
- `niveau`
- `titre`
- `message`
- `ressource_type`
- `ressource_id`
- `responsable_id` — FK vers `utilisateurs.id`, facultatif
- `date_detection`
- `date_resolution`
- `regle_notification`
- `statut`

### 53. notifications

- `id` — PK
- `alerte_id` — FK vers `alertes.id`, facultatif
- `destinataire_utilisateur_id` — FK vers `utilisateurs.id`, facultatif
- `adresse_externe`
- `canal`
- `objet`
- `contenu`
- `date_envoi`
- `date_lecture`
- `resultat`
- `nombre_tentatives`
- `message_erreur`
- `statut`

### 54. dossiers_veille

- `id` — PK
- `certification_id` — FK vers `certifications.id`
- `type_evenement`
- `priorite`
- `date_ouverture`
- `responsable_id` — FK vers `utilisateurs.id`
- `prochaine_action_at`
- `date_cloture`
- `statut`

### 55. relances_veille

- `id` — PK
- `dossier_veille_id` — FK vers `dossiers_veille.id`
- `destinataire`
- `canal`
- `objet`
- `date_envoi`
- `date_echeance`
- `date_reponse`
- `reponse`
- `resultat`
- `statut`

### 56. rapports_veille

- `id` — PK
- `type_rapport`
- `periode_debut`
- `periode_fin`
- `nombre_certifications_suivies`
- `nombre_alertes`
- `nombre_renouvellements`
- `delai_moyen_traitement`
- `indicateurs`
- `prepare_par_id` — FK vers `utilisateurs.id`
- `valide_par_id` — FK vers `utilisateurs.id`, facultatif
- `date_validation`
- `statut`

## 10. Gouvernance, qualité et rapports

### 57. regles_metier

- `id` — PK
- `code` — UQ
- `famille`
- `libelle`
- `description`
- `version`
- `parametres`
- `date_debut_effet`
- `date_fin_effet`
- `reference_approbation`
- `approuve_par_id` — FK vers `utilisateurs.id`, facultatif
- `statut`

### 58. revues_qualite

- `id` — PK
- `periode_debut`
- `periode_fin`
- `perimetre`
- `resultat_global`
- `constats`
- `preuves`
- `responsable_id` — FK vers `utilisateurs.id`
- `date_validation`
- `statut`

### 59. plans_action

- `id` — PK
- `revue_qualite_id` — FK vers `revues_qualite.id`, facultatif
- `titre`
- `objectif`
- `responsable_id` — FK vers `utilisateurs.id`
- `date_debut`
- `date_echeance`
- `priorite`
- `indicateur`
- `progression`
- `date_cloture`
- `statut`

### 60. decisions_institutionnelles

- `id` — PK
- `ressource_type`
- `ressource_id`
- `type_decision`
- `titre`
- `contexte`
- `constats`
- `risques`
- `options`
- `decision`
- `recommandation`
- `autorite`
- `decide_par_id` — FK vers `utilisateurs.id`, facultatif
- `date_decision`
- `priorite`
- `statut`

### 61. publications

- `id` — PK
- `ressource_type`
- `ressource_id`
- `objet`
- `perimetre`
- `niveau_confidentialite`
- `demande_par_id` — FK vers `utilisateurs.id`
- `date_demande`
- `decision`
- `autorite_approbation`
- `approuve_par_id` — FK vers `utilisateurs.id`, facultatif
- `date_approbation`
- `reserve`
- `date_publication`
- `statut`

### 62. rapports_generes

- `id` — PK
- `code_modele`
- `nom_modele`
- `categorie`
- `demandeur_id` — FK vers `utilisateurs.id`
- `filtres`
- `sections`
- `format`
- `periode_debut`
- `periode_fin`
- `date_demande`
- `date_generation`
- `document_id` — FK vers `documents.id`, facultatif
- `resultat`
- `statut`

## 11. Audit, archivage, sauvegardes et incidents

### 63. evenements_audit

- `id` — PK
- `utilisateur_id` — FK vers `utilisateurs.id`, facultatif
- `action`
- `categorie`
- `ressource_type`
- `ressource_id`
- `adresse_ip`
- `contexte`
- `valeurs_avant`
- `valeurs_apres`
- `empreinte`
- `resultat`
- `date_evenement`

### 64. archives

- `id` — PK
- `ressource_type`
- `ressource_id`
- `categorie_donnees`
- `date_archivage`
- `motif`
- `auteur_id` — FK vers `utilisateurs.id`
- `duree_conservation`
- `date_suppression_prevue`
- `emplacement`
- `statut`

### 65. sauvegardes

- `id` — PK
- `type_enregistrement` — politique, exécution ou test
- `parent_id` — FK récursive facultative
- `frequence`
- `retention`
- `perimetre`
- `emplacement_stockage`
- `date_debut`
- `date_fin`
- `taille_octets`
- `integrite_validee`
- `resultat`
- `preuve_document_id` — FK vers `documents.id`, facultatif
- `message_erreur`
- `statut`

### 66. incidents

- `id` — PK
- `code` — UQ
- `categorie`
- `gravite`
- `titre`
- `description`
- `date_declaration`
- `declare_par_id` — FK vers `utilisateurs.id`
- `responsable_id` — FK vers `utilisateurs.id`, facultatif
- `ressource_type`
- `ressource_id`
- `preuves`
- `resolution`
- `date_resolution`
- `date_cloture`
- `statut`

## Points de validation

Avant de produire le MLD et les modèles SQLAlchemy, il reste à valider :

1. les champs réellement obligatoires ;
2. les listes de valeurs contrôlées ;
3. les informations sensibles ou confidentielles ;
4. les cardinalités entre les tables ;
5. les champs multivalués à conserver en tables ou en `JSONB` ;
6. les durées de conservation et règles d’archivage ;
7. la correspondance avec chaque champ du frontend et de la fiche officielle.
