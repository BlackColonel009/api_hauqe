# Dictionnaire de données — HAUQE Certif

**Version :** 0.3  
**Cible :** PostgreSQL / FastAPI / PowerDesigner  
**Nombre de tables :** 66  
**Nombre de clés étrangères :** 107  

Ce document reprend exactement les tables et colonnes générées dans `output/sql/HAUQE_CERTIF_POWERDESIGNER.sql`.

Abréviations : `PK` = clé primaire, `FK` = clé étrangère, `UQ` = contrainte d’unicité, `NN` = obligatoire.

## 1. `utilisateurs`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `email` | `VARCHAR(255)` | UQ, NN |
| `mot_de_passe_hash` | `VARCHAR(255)` | — |
| `nom` | `VARCHAR(255)` | — |
| `prenoms` | `VARCHAR(255)` | — |
| `telephone` | `VARCHAR(255)` | — |
| `fonction` | `VARCHAR(255)` | — |
| `region_affectation_id` | `UUID` | FK → `zones_administratives.id`, facultatif |
| `statut` | `VARCHAR(255)` | — |
| `mfa_active` | `BOOLEAN` | — |
| `derniere_connexion_at` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 2. `roles`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `niveau` | `INTEGER` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 3. `permissions`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `domaine` | `VARCHAR(255)` | — |
| `action` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 4. `utilisateur_role`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `utilisateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `role_id` | `UUID` | FK → `roles.id`, NN |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `attribue_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `motif` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 5. `role_permission`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `role_id` | `UUID` | FK → `roles.id`, NN |
| `permission_id` | `UUID` | FK → `permissions.id`, NN |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 6. `sessions_utilisateur`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `utilisateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `jeton_hash` | `VARCHAR(255)` | — |
| `adresse_ip` | `VARCHAR(255)` | — |
| `user_agent` | `VARCHAR(255)` | — |
| `debut_at` | `TIMESTAMPTZ` | — |
| `derniere_activite_at` | `TIMESTAMPTZ` | — |
| `expiration_at` | `TIMESTAMPTZ` | — |
| `revoquee_at` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 7. `zones_administratives`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `parent_id` | `UUID` | FK → `zones_administratives.id`, facultatif |
| `type_zone` | `VARCHAR(255)` | — |
| `code` | `VARCHAR(255)` | — |
| `nom` | `VARCHAR(255)` | — |
| `latitude` | `NUMERIC(18,4)` | — |
| `longitude` | `NUMERIC(18,4)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 8. `referentiels`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `type_valeur` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 9. `valeurs_referentiel`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `referentiel_id` | `UUID` | FK → `referentiels.id`, NN |
| `parent_id` | `UUID` | FK → `valeurs_referentiel.id`, facultatif |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `ordre_affichage` | `INTEGER` | — |
| `date_debut_validite` | `DATE` | — |
| `date_fin_validite` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 10. `normes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | — |
| `nom` | `VARCHAR(255)` | — |
| `version` | `VARCHAR(255)` | — |
| `autorite_emettrice` | `VARCHAR(255)` | — |
| `domaine` | `VARCHAR(255)` | — |
| `portee` | `TEXT` | — |
| `date_debut_application` | `DATE` | — |
| `date_fin_application` | `DATE` | — |
| `date_expiration` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 11. `entreprises`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `identifiant_national` | `VARCHAR(255)` | UQ, NN |
| `raison_sociale` | `VARCHAR(255)` | — |
| `nom_commercial` | `VARCHAR(255)` | — |
| `forme_juridique` | `VARCHAR(255)` | — |
| `rccm` | `VARCHAR(255)` | — |
| `nif` | `VARCHAR(255)` | — |
| `ifu` | `VARCHAR(255)` | — |
| `date_creation` | `DATE` | — |
| `nationalite` | `VARCHAR(255)` | — |
| `capital_social` | `NUMERIC(18,4)` | — |
| `effectif` | `INTEGER` | — |
| `chiffre_affaires` | `NUMERIC(18,4)` | — |
| `email_principal` | `VARCHAR(255)` | — |
| `telephone_principal` | `VARCHAR(255)` | — |
| `site_web` | `VARCHAR(255)` | — |
| `adresse_siege` | `VARCHAR(255)` | — |
| `zone_siege_id` | `UUID` | FK → `zones_administratives.id`, NN |
| `activite_principale` | `VARCHAR(255)` | — |
| `secteurs_secondaires` | `JSONB` | — |
| `statut` | `VARCHAR(255)` | — |
| `niveau_risque` | `VARCHAR(255)` | — |
| `source_donnee` | `VARCHAR(255)` | — |
| `date_derniere_verification` | `DATE` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 12. `contacts_entreprise`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, NN |
| `nom` | `VARCHAR(255)` | — |
| `prenoms` | `VARCHAR(255)` | — |
| `fonction` | `VARCHAR(255)` | — |
| `telephone` | `VARCHAR(255)` | — |
| `email` | `VARCHAR(255)` | — |
| `type_contact` | `VARCHAR(255)` | — |
| `contact_principal` | `BOOLEAN` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 13. `sites_entreprise`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, NN |
| `nom` | `VARCHAR(255)` | — |
| `type_site` | `VARCHAR(255)` | — |
| `adresse` | `TEXT` | — |
| `zone_id` | `UUID` | FK → `zones_administratives.id`, NN |
| `latitude` | `NUMERIC(18,4)` | — |
| `longitude` | `NUMERIC(18,4)` | — |
| `date_ouverture` | `DATE` | — |
| `effectif` | `INTEGER` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 14. `offres_entreprise`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, NN |
| `type_offre` | `VARCHAR(255)` | — |
| `nom` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `categorie` | `VARCHAR(255)` | — |
| `volume_annuel` | `NUMERIC(18,4)` | — |
| `unite` | `VARCHAR(255)` | — |
| `capacite_production` | `NUMERIC(18,4)` | — |
| `marches_cibles` | `JSONB` | — |
| `destinations` | `JSONB` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 15. `candidats_doublon`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `entreprise_source_id` | `UUID` | FK → `entreprises.id`, NN |
| `entreprise_cible_id` | `UUID` | FK → `entreprises.id`, NN |
| `criteres_concordants` | `JSONB` | — |
| `score_similarite` | `NUMERIC(18,4)` | — |
| `statut_examen` | `VARCHAR(255)` | — |
| `decision` | `VARCHAR(255)` | — |
| `motif_decision` | `VARCHAR(255)` | — |
| `examine_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `examine_at` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 16. `organismes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `identifiant_national` | `VARCHAR(255)` | — |
| `nom_officiel` | `VARCHAR(255)` | — |
| `sigle` | `VARCHAR(255)` | — |
| `type_organisme` | `VARCHAR(255)` | — |
| `pays` | `VARCHAR(255)` | — |
| `numero_enregistrement` | `VARCHAR(255)` | — |
| `email` | `VARCHAR(255)` | — |
| `telephone` | `VARCHAR(255)` | — |
| `adresse` | `TEXT` | — |
| `zone_id` | `UUID` | FK → `zones_administratives.id`, facultatif |
| `site_web` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `date_derniere_verification` | `DATE` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 17. `accreditations`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `organisme_id` | `UUID` | FK → `organismes.id`, NN |
| `numero` | `VARCHAR(255)` | — |
| `accrediteur` | `VARCHAR(255)` | — |
| `domaine_technique` | `VARCHAR(255)` | — |
| `perimetre` | `TEXT` | — |
| `date_delivrance` | `DATE` | — |
| `date_expiration` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `reference_officielle` | `VARCHAR(255)` | — |
| `decision_hauqe` | `VARCHAR(255)` | — |
| `date_decision` | `DATE` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 18. `certifications`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `identifiant_national` | `VARCHAR(255)` | UQ, NN |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, NN |
| `organisme_id` | `UUID` | FK → `organismes.id`, NN |
| `accreditation_id` | `UUID` | FK → `accreditations.id`, facultatif |
| `norme_id` | `UUID` | FK → `normes.id`, NN |
| `numero_certificat` | `VARCHAR(255)` | — |
| `portee` | `TEXT` | — |
| `date_obtention` | `DATE` | — |
| `date_effet` | `DATE` | — |
| `date_expiration` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `motif_statut` | `VARCHAR(255)` | — |
| `classification` | `VARCHAR(255)` | — |
| `authenticite_verifiee` | `BOOLEAN` | — |
| `certification_strategique` | `BOOLEAN` | — |
| `source_donnee` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 19. `couvertures_certification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `type_couverture` | `VARCHAR(255)` | — |
| `offre_entreprise_id` | `UUID` | FK → `offres_entreprise.id`, facultatif |
| `site_entreprise_id` | `UUID` | FK → `sites_entreprise.id`, facultatif |
| `libelle_couverture` | `VARCHAR(255)` | — |
| `details` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 20. `audits_certification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `type_audit` | `VARCHAR(255)` | — |
| `date_prevue` | `DATE` | — |
| `date_realisee` | `DATE` | — |
| `auditeur` | `VARCHAR(255)` | — |
| `resultat` | `TEXT` | — |
| `prochain_audit_at` | `TIMESTAMPTZ` | — |
| `observations` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 21. `evenements_certification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `type_evenement` | `VARCHAR(255)` | — |
| `ancien_statut` | `VARCHAR(255)` | — |
| `nouveau_statut` | `VARCHAR(255)` | — |
| `date_evenement` | `TIMESTAMPTZ` | — |
| `motif` | `TEXT` | — |
| `source` | `VARCHAR(255)` | — |
| `acteur_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 22. `renouvellements_certification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `date_ouverture` | `DATE` | — |
| `date_limite` | `DATE` | — |
| `date_decision` | `DATE` | — |
| `decision` | `VARCHAR(255)` | — |
| `resultat` | `TEXT` | — |
| `justification` | `TEXT` | — |
| `preuves` | `JSONB` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 23. `documents`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `type_document` | `VARCHAR(255)` | — |
| `nom_original` | `VARCHAR(255)` | — |
| `nom_stockage` | `VARCHAR(255)` | — |
| `chemin_stockage` | `VARCHAR(255)` | — |
| `format` | `VARCHAR(255)` | — |
| `taille_octets` | `BIGINT` | — |
| `checksum` | `VARCHAR(255)` | — |
| `version` | `VARCHAR(255)` | — |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `confidentialite` | `VARCHAR(255)` | — |
| `source` | `VARCHAR(255)` | — |
| `date_document` | `DATE` | — |
| `depose_par_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `date_depot` | `TIMESTAMPTZ` | — |
| `statut_verification` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 24. `campagnes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `nom` | `VARCHAR(255)` | — |
| `objet` | `VARCHAR(255)` | — |
| `objectif` | `VARCHAR(255)` | — |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 25. `missions_collecte`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `campagne_id` | `UUID` | FK → `campagnes.id`, NN |
| `code` | `VARCHAR(255)` | — |
| `objet` | `VARCHAR(255)` | — |
| `zone_id` | `UUID` | FK → `zones_administratives.id`, NN |
| `date_debut_prevue` | `DATE` | — |
| `date_fin_prevue` | `DATE` | — |
| `date_debut_reelle` | `DATE` | — |
| `date_fin_reelle` | `DATE` | — |
| `priorite` | `VARCHAR(255)` | — |
| `progression` | `INTEGER` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 26. `affectations_mission`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `mission_id` | `UUID` | FK → `missions_collecte.id`, NN |
| `utilisateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `role_mission` | `VARCHAR(255)` | — |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `attribue_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `motif` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 27. `fiches_collecte`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `mission_id` | `UUID` | FK → `missions_collecte.id`, NN |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, facultatif |
| `version_formulaire` | `VARCHAR(255)` | — |
| `numero_revision` | `INTEGER` | — |
| `statut` | `VARCHAR(255)` | — |
| `taux_completude` | `NUMERIC(18,4)` | — |
| `consentement_obtenu` | `BOOLEAN` | — |
| `nom_declarant` | `VARCHAR(255)` | — |
| `fonction_declarant` | `VARCHAR(255)` | — |
| `telephone_declarant` | `VARCHAR(255)` | — |
| `email_declarant` | `VARCHAR(255)` | — |
| `signature_declarant` | `VARCHAR(255)` | — |
| `observations` | `TEXT` | — |
| `collecte_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `collecte_at` | `TIMESTAMPTZ` | — |
| `soumise_at` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 28. `offres_declarees`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `fiche_collecte_id` | `UUID` | FK → `fiches_collecte.id`, NN |
| `type_offre` | `VARCHAR(255)` | — |
| `nom` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `categorie` | `VARCHAR(255)` | — |
| `volume` | `NUMERIC(18,4)` | — |
| `unite` | `VARCHAR(255)` | — |
| `capacite` | `NUMERIC(18,4)` | — |
| `marches_vises` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 29. `certifications_declarees`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `fiche_collecte_id` | `UUID` | FK → `fiches_collecte.id`, NN |
| `nom_certification` | `VARCHAR(255)` | — |
| `numero` | `VARCHAR(255)` | — |
| `organisme_declare` | `VARCHAR(255)` | — |
| `norme_declaree` | `VARCHAR(255)` | — |
| `portee` | `TEXT` | — |
| `date_obtention` | `DATE` | — |
| `date_expiration` | `DATE` | — |
| `copie_disponible` | `BOOLEAN` | — |
| `certification_officielle_id` | `UUID` | FK → `certifications.id`, facultatif |
| `score_rapprochement` | `NUMERIC(18,4)` | — |
| `statut_rapprochement` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 30. `evenements_collecte`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `fiche_collecte_id` | `UUID` | FK → `fiches_collecte.id`, NN |
| `type_evenement` | `VARCHAR(255)` | — |
| `ancien_statut` | `VARCHAR(255)` | — |
| `nouveau_statut` | `VARCHAR(255)` | — |
| `commentaire` | `TEXT` | — |
| `acteur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_evenement` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 31. `dossiers_verification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `fiche_collecte_id` | `UUID` | FK → `fiches_collecte.id`, NN |
| `date_ouverture` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `avis` | `VARCHAR(255)` | — |
| `synthese` | `TEXT` | — |
| `niveau_risque` | `VARCHAR(255)` | — |
| `priorite` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 32. `affectations_verification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_verification_id` | `UUID` | FK → `dossiers_verification.id`, NN |
| `verificateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `date_echeance` | `DATE` | — |
| `motif` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 33. `points_verification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_verification_id` | `UUID` | FK → `dossiers_verification.id`, NN |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `categorie` | `VARCHAR(255)` | — |
| `resultat` | `TEXT` | — |
| `observation` | `TEXT` | — |
| `date_verification` | `DATE` | — |
| `preuve_document_id` | `UUID` | FK → `documents.id`, facultatif |
| `verifie_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 34. `anomalies_verification`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_verification_id` | `UUID` | FK → `dossiers_verification.id`, NN |
| `point_verification_id` | `UUID` | FK → `points_verification.id`, facultatif |
| `categorie` | `VARCHAR(255)` | — |
| `gravite` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `resolution` | `TEXT` | — |
| `date_resolution` | `DATE` | — |
| `escalade` | `BOOLEAN` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 35. `confirmations_externes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_verification_id` | `UUID` | FK → `dossiers_verification.id`, NN |
| `organisme_id` | `UUID` | FK → `organismes.id`, facultatif |
| `canal` | `VARCHAR(255)` | — |
| `destinataire` | `VARCHAR(255)` | — |
| `objet` | `VARCHAR(255)` | — |
| `date_envoi` | `DATE` | — |
| `date_echeance` | `DATE` | — |
| `date_reponse` | `DATE` | — |
| `contenu_reponse` | `TEXT` | — |
| `resultat` | `TEXT` | — |
| `document_id` | `UUID` | FK → `documents.id`, facultatif |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 36. `grilles_fuccs`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `version` | `VARCHAR(255)` | — |
| `date_effet` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `reference_approbation` | `VARCHAR(255)` | — |
| `statut_publication` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 37. `rubriques_fuccs`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `grille_fuccs_id` | `UUID` | FK → `grilles_fuccs.id`, NN |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `ordre_affichage` | `INTEGER` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 38. `criteres_fuccs`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `rubrique_fuccs_id` | `UUID` | FK → `rubriques_fuccs.id`, NN |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `score_maximal` | `NUMERIC(18,4)` | — |
| `poids` | `NUMERIC(18,4)` | — |
| `ordre_affichage` | `INTEGER` | — |
| `commentaire_obligatoire` | `BOOLEAN` | — |
| `preuve_obligatoire` | `BOOLEAN` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 39. `controles_fuccs`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_verification_id` | `UUID` | FK → `dossiers_verification.id`, NN |
| `grille_fuccs_id` | `UUID` | FK → `grilles_fuccs.id`, NN |
| `controleur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `score_brut` | `NUMERIC(18,4)` | — |
| `score_maximal` | `NUMERIC(18,4)` | — |
| `taux` | `VARCHAR(255)` | — |
| `synthese` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 40. `notes_criteres`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `controle_fuccs_id` | `UUID` | FK → `controles_fuccs.id`, NN |
| `critere_fuccs_id` | `UUID` | FK → `criteres_fuccs.id`, NN |
| `score` | `NUMERIC(18,4)` | — |
| `commentaire` | `TEXT` | — |
| `preuve_document_id` | `UUID` | FK → `documents.id`, facultatif |
| `note_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 41. `constats_controle`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `controle_fuccs_id` | `UUID` | FK → `controles_fuccs.id`, NN |
| `type_constat` | `VARCHAR(255)` | — |
| `gravite` | `VARCHAR(255)` | — |
| `titre` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 42. `validations`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `fiche_collecte_id` | `UUID` | FK → `fiches_collecte.id`, NN |
| `controle_fuccs_id` | `UUID` | FK → `controles_fuccs.id`, facultatif |
| `niveau_validation` | `VARCHAR(255)` | — |
| `validateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `decision` | `VARCHAR(255)` | — |
| `date_validation` | `DATE` | — |
| `reserves` | `VARCHAR(255)` | — |
| `justification` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 43. `corrections`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `validation_id` | `UUID` | FK → `validations.id`, NN |
| `motif` | `TEXT` | — |
| `instructions` | `TEXT` | — |
| `date_demande` | `DATE` | — |
| `date_echeance` | `DATE` | — |
| `date_resoumission` | `DATE` | — |
| `reponse` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 44. `integrations_bnec`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `validation_id` | `UUID` | FK → `validations.id`, NN |
| `administrateur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `precontrole` | `VARCHAR(255)` | — |
| `postcontrole` | `VARCHAR(255)` | — |
| `sauvegarde_reference` | `VARCHAR(255)` | — |
| `resume` | `TEXT` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 45. `elements_integration`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `integration_bnec_id` | `UUID` | FK → `integrations_bnec.id`, NN |
| `type_objet` | `VARCHAR(255)` | — |
| `ressource_source_id` | `UUID` | — |
| `ressource_cible_id` | `UUID` | — |
| `revision_source` | `VARCHAR(255)` | — |
| `action` | `VARCHAR(255)` | — |
| `code_genere` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `message_erreur` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 46. `modeles_scoring`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `version` | `VARCHAR(255)` | — |
| `objet_evalue` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `date_debut_validite` | `DATE` | — |
| `date_fin_validite` | `DATE` | — |
| `regle_calcul` | `TEXT` | — |
| `reference_approbation` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 47. `ponderations_scoring`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `modele_scoring_id` | `UUID` | FK → `modeles_scoring.id`, NN |
| `domaine` | `VARCHAR(255)` | — |
| `valeur` | `NUMERIC(18,4)` | — |
| `periode_debut` | `VARCHAR(255)` | — |
| `periode_fin` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 48. `classifications_entreprise`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `entreprise_id` | `UUID` | FK → `entreprises.id`, NN |
| `modele_scoring_id` | `UUID` | FK → `modeles_scoring.id`, NN |
| `score` | `NUMERIC(18,4)` | — |
| `classe` | `VARCHAR(255)` | — |
| `date_calcul` | `DATE` | — |
| `date_validation` | `DATE` | — |
| `sources` | `JSONB` | — |
| `valide_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 49. `resultats_infc`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `modele_scoring_id` | `UUID` | FK → `modeles_scoring.id`, NN |
| `score_global` | `NUMERIC(18,4)` | — |
| `niveau` | `INTEGER` | — |
| `scores_domaines` | `JSONB` | — |
| `date_calcul` | `DATE` | — |
| `date_validation` | `DATE` | — |
| `sources` | `JSONB` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 50. `classements_sncc`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `classe` | `VARCHAR(255)` | — |
| `statut_administratif` | `VARCHAR(255)` | — |
| `niveau_risque` | `VARCHAR(255)` | — |
| `justification` | `TEXT` | — |
| `date_effet` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `valide_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 51. `echeances`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `type_echeance` | `VARCHAR(255)` | — |
| `titre` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `date_echeance` | `DATE` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `priorite` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 52. `alertes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `echeance_id` | `UUID` | FK → `echeances.id`, facultatif |
| `type_alerte` | `VARCHAR(255)` | — |
| `niveau` | `INTEGER` | — |
| `titre` | `VARCHAR(255)` | — |
| `message` | `TEXT` | — |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `date_detection` | `DATE` | — |
| `date_resolution` | `DATE` | — |
| `regle_notification` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 53. `notifications`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `alerte_id` | `UUID` | FK → `alertes.id`, facultatif |
| `destinataire_utilisateur_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `adresse_externe` | `VARCHAR(255)` | — |
| `canal` | `VARCHAR(255)` | — |
| `objet` | `VARCHAR(255)` | — |
| `contenu` | `TEXT` | — |
| `date_envoi` | `DATE` | — |
| `date_lecture` | `DATE` | — |
| `resultat` | `TEXT` | — |
| `nombre_tentatives` | `INTEGER` | — |
| `message_erreur` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 54. `dossiers_veille`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `certification_id` | `UUID` | FK → `certifications.id`, NN |
| `type_evenement` | `VARCHAR(255)` | — |
| `priorite` | `VARCHAR(255)` | — |
| `date_ouverture` | `DATE` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `prochaine_action_at` | `TIMESTAMPTZ` | — |
| `date_cloture` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 55. `relances_veille`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `dossier_veille_id` | `UUID` | FK → `dossiers_veille.id`, NN |
| `destinataire` | `VARCHAR(255)` | — |
| `canal` | `VARCHAR(255)` | — |
| `objet` | `VARCHAR(255)` | — |
| `date_envoi` | `DATE` | — |
| `date_echeance` | `DATE` | — |
| `date_reponse` | `DATE` | — |
| `reponse` | `TEXT` | — |
| `resultat` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 56. `rapports_veille`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `type_rapport` | `VARCHAR(255)` | — |
| `periode_debut` | `VARCHAR(255)` | — |
| `periode_fin` | `VARCHAR(255)` | — |
| `nombre_certifications_suivies` | `INTEGER` | — |
| `nombre_alertes` | `INTEGER` | — |
| `nombre_renouvellements` | `INTEGER` | — |
| `delai_moyen_traitement` | `NUMERIC(18,4)` | — |
| `indicateurs` | `JSONB` | — |
| `prepare_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `valide_par_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `date_validation` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 57. `regles_metier`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `famille` | `VARCHAR(255)` | — |
| `libelle` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `version` | `VARCHAR(255)` | — |
| `parametres` | `JSONB` | — |
| `date_debut_effet` | `DATE` | — |
| `date_fin_effet` | `DATE` | — |
| `reference_approbation` | `VARCHAR(255)` | — |
| `approuve_par_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 58. `revues_qualite`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `periode_debut` | `VARCHAR(255)` | — |
| `periode_fin` | `VARCHAR(255)` | — |
| `perimetre` | `TEXT` | — |
| `resultat_global` | `VARCHAR(255)` | — |
| `constats` | `JSONB` | — |
| `preuves` | `JSONB` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_validation` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 59. `plans_action`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `revue_qualite_id` | `UUID` | FK → `revues_qualite.id`, facultatif |
| `titre` | `VARCHAR(255)` | — |
| `objectif` | `VARCHAR(255)` | — |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_debut` | `DATE` | — |
| `date_echeance` | `DATE` | — |
| `priorite` | `VARCHAR(255)` | — |
| `indicateur` | `VARCHAR(255)` | — |
| `progression` | `INTEGER` | — |
| `date_cloture` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 60. `decisions_institutionnelles`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `type_decision` | `VARCHAR(255)` | — |
| `titre` | `VARCHAR(255)` | — |
| `contexte` | `TEXT` | — |
| `constats` | `JSONB` | — |
| `risques` | `VARCHAR(255)` | — |
| `options` | `VARCHAR(255)` | — |
| `decision` | `VARCHAR(255)` | — |
| `recommandation` | `VARCHAR(255)` | — |
| `autorite` | `VARCHAR(255)` | — |
| `decide_par_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `date_decision` | `DATE` | — |
| `priorite` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 61. `publications`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `objet` | `VARCHAR(255)` | — |
| `perimetre` | `TEXT` | — |
| `niveau_confidentialite` | `VARCHAR(255)` | — |
| `demande_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `date_demande` | `DATE` | — |
| `decision` | `VARCHAR(255)` | — |
| `autorite_approbation` | `VARCHAR(255)` | — |
| `approuve_par_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `date_approbation` | `DATE` | — |
| `reserve` | `VARCHAR(255)` | — |
| `date_publication` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 62. `rapports_generes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code_modele` | `VARCHAR(255)` | — |
| `nom_modele` | `VARCHAR(255)` | — |
| `categorie` | `VARCHAR(255)` | — |
| `demandeur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `filtres` | `JSONB` | — |
| `sections` | `JSONB` | — |
| `format` | `VARCHAR(255)` | — |
| `periode_debut` | `VARCHAR(255)` | — |
| `periode_fin` | `VARCHAR(255)` | — |
| `date_demande` | `DATE` | — |
| `date_generation` | `DATE` | — |
| `document_id` | `UUID` | FK → `documents.id`, facultatif |
| `resultat` | `TEXT` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 63. `evenements_audit`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `utilisateur_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `action` | `VARCHAR(255)` | — |
| `categorie` | `VARCHAR(255)` | — |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `adresse_ip` | `VARCHAR(255)` | — |
| `contexte` | `TEXT` | — |
| `valeurs_avant` | `JSONB` | — |
| `valeurs_apres` | `JSONB` | — |
| `empreinte` | `VARCHAR(255)` | — |
| `resultat` | `TEXT` | — |
| `date_evenement` | `TIMESTAMPTZ` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 64. `archives`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `categorie_donnees` | `VARCHAR(255)` | — |
| `date_archivage` | `TIMESTAMPTZ` | — |
| `motif` | `TEXT` | — |
| `auteur_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `duree_conservation` | `VARCHAR(255)` | — |
| `date_suppression_prevue` | `DATE` | — |
| `emplacement` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 65. `sauvegardes`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `type_enregistrement` | `VARCHAR(255)` | — |
| `parent_id` | `UUID` | FK → `sauvegardes.id`, facultatif |
| `frequence` | `VARCHAR(255)` | — |
| `retention` | `VARCHAR(255)` | — |
| `perimetre` | `TEXT` | — |
| `emplacement_stockage` | `VARCHAR(255)` | — |
| `date_debut` | `DATE` | — |
| `date_fin` | `DATE` | — |
| `taille_octets` | `BIGINT` | — |
| `integrite_validee` | `BOOLEAN` | — |
| `resultat` | `TEXT` | — |
| `preuve_document_id` | `UUID` | FK → `documents.id`, facultatif |
| `message_erreur` | `VARCHAR(255)` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## 66. `incidents`

| Colonne | Type PostgreSQL | Contraintes / relation |
|---|---|---|
| `id` | `UUID` | PK, NN, `gen_random_uuid()` |
| `code` | `VARCHAR(255)` | UQ, NN |
| `categorie` | `VARCHAR(255)` | — |
| `gravite` | `VARCHAR(255)` | — |
| `titre` | `VARCHAR(255)` | — |
| `description` | `TEXT` | — |
| `date_declaration` | `DATE` | — |
| `declare_par_id` | `UUID` | FK → `utilisateurs.id`, NN |
| `responsable_id` | `UUID` | FK → `utilisateurs.id`, facultatif |
| `ressource_type` | `VARCHAR(255)` | — |
| `ressource_id` | `UUID` | — |
| `preuves` | `JSONB` | — |
| `resolution` | `TEXT` | — |
| `date_resolution` | `DATE` | — |
| `date_cloture` | `DATE` | — |
| `statut` | `VARCHAR(255)` | — |
| `created_at` | `TIMESTAMPTZ` | NN, `now()` |
| `updated_at` | `TIMESTAMPTZ` | NN, `now()` |

## Synthèse

- Tables : **66**
- Colonnes totales : **843**
- Clés étrangères : **107**
- Contraintes d’unicité : **9**
- Champs techniques automatiques : `created_at` et `updated_at` sur chaque table.
