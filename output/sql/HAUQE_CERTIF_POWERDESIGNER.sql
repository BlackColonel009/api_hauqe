-- HAUQE Certif - Schéma PostgreSQL destiné à la rétroconception PowerDesigner
-- Généré depuis MODELE_TABLES_VARIABLES_V2.md
-- PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS hauqe_certif;
SET search_path TO hauqe_certif, public;

CREATE TABLE "utilisateurs" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "email" VARCHAR(255) NOT NULL,
    "mot_de_passe_hash" VARCHAR(255),
    "nom" VARCHAR(255),
    "prenoms" VARCHAR(255),
    "telephone" VARCHAR(255),
    "fonction" VARCHAR(255),
    "region_affectation_id" UUID,
    "statut" VARCHAR(255),
    "mfa_active" BOOLEAN,
    "derniere_connexion_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "utilisateurs" IS 'Table métier HAUQE Certif';

CREATE TABLE "roles" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "libelle" VARCHAR(255),
    "description" TEXT,
    "niveau" INTEGER,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "roles" IS 'Table métier HAUQE Certif';

CREATE TABLE "permissions" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "domaine" VARCHAR(255),
    "action" VARCHAR(255),
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "permissions" IS 'Table métier HAUQE Certif';

CREATE TABLE "utilisateur_role" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "utilisateur_id" UUID NOT NULL,
    "role_id" UUID NOT NULL,
    "date_debut" DATE,
    "date_fin" DATE,
    "attribue_par_id" UUID NOT NULL,
    "motif" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "utilisateur_role" IS 'Table métier HAUQE Certif';

CREATE TABLE "role_permission" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "role_id" UUID NOT NULL,
    "permission_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "role_permission" IS 'Table métier HAUQE Certif';

CREATE TABLE "sessions_utilisateur" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "utilisateur_id" UUID NOT NULL,
    "jeton_hash" VARCHAR(255),
    "adresse_ip" VARCHAR(255),
    "user_agent" VARCHAR(255),
    "debut_at" TIMESTAMPTZ,
    "derniere_activite_at" TIMESTAMPTZ,
    "expiration_at" TIMESTAMPTZ,
    "revoquee_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "sessions_utilisateur" IS 'Table métier HAUQE Certif';

CREATE TABLE "zones_administratives" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "parent_id" UUID,
    "type_zone" VARCHAR(255),
    "code" VARCHAR(255),
    "nom" VARCHAR(255),
    "latitude" NUMERIC(18,4),
    "longitude" NUMERIC(18,4),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "zones_administratives" IS 'Table métier HAUQE Certif';

CREATE TABLE "referentiels" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "libelle" VARCHAR(255),
    "description" TEXT,
    "type_valeur" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "referentiels" IS 'Table métier HAUQE Certif';

CREATE TABLE "valeurs_referentiel" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "referentiel_id" UUID NOT NULL,
    "parent_id" UUID,
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "description" TEXT,
    "ordre_affichage" INTEGER,
    "date_debut_validite" DATE,
    "date_fin_validite" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "valeurs_referentiel" IS 'Table métier HAUQE Certif';

CREATE TABLE "normes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255),
    "nom" VARCHAR(255),
    "version" VARCHAR(255),
    "autorite_emettrice" VARCHAR(255),
    "domaine" VARCHAR(255),
    "portee" TEXT,
    "date_debut_application" DATE,
    "date_fin_application" DATE,
    "date_expiration" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "normes" IS 'Table métier HAUQE Certif';

CREATE TABLE "entreprises" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "identifiant_national" VARCHAR(255) NOT NULL,
    "raison_sociale" VARCHAR(255),
    "nom_commercial" VARCHAR(255),
    "forme_juridique" VARCHAR(255),
    "rccm" VARCHAR(255),
    "nif" VARCHAR(255),
    "ifu" VARCHAR(255),
    "date_creation" DATE,
    "nationalite" VARCHAR(255),
    "capital_social" NUMERIC(18,4),
    "effectif" INTEGER,
    "chiffre_affaires" NUMERIC(18,4),
    "email_principal" VARCHAR(255),
    "telephone_principal" VARCHAR(255),
    "site_web" VARCHAR(255),
    "adresse_siege" VARCHAR(255),
    "zone_siege_id" UUID NOT NULL,
    "activite_principale" VARCHAR(255),
    "secteurs_secondaires" JSONB,
    "statut" VARCHAR(255),
    "niveau_risque" VARCHAR(255),
    "source_donnee" VARCHAR(255),
    "date_derniere_verification" DATE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "entreprises" IS 'Table métier HAUQE Certif';

CREATE TABLE "contacts_entreprise" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "entreprise_id" UUID NOT NULL,
    "nom" VARCHAR(255),
    "prenoms" VARCHAR(255),
    "fonction" VARCHAR(255),
    "telephone" VARCHAR(255),
    "email" VARCHAR(255),
    "type_contact" VARCHAR(255),
    "contact_principal" BOOLEAN,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "contacts_entreprise" IS 'Table métier HAUQE Certif';

CREATE TABLE "sites_entreprise" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "entreprise_id" UUID NOT NULL,
    "nom" VARCHAR(255),
    "type_site" VARCHAR(255),
    "adresse" TEXT,
    "zone_id" UUID NOT NULL,
    "latitude" NUMERIC(18,4),
    "longitude" NUMERIC(18,4),
    "date_ouverture" DATE,
    "effectif" INTEGER,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "sites_entreprise" IS 'Table métier HAUQE Certif';

CREATE TABLE "offres_entreprise" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "entreprise_id" UUID NOT NULL,
    "type_offre" VARCHAR(255),
    "nom" VARCHAR(255),
    "description" TEXT,
    "categorie" VARCHAR(255),
    "volume_annuel" NUMERIC(18,4),
    "unite" VARCHAR(255),
    "capacite_production" NUMERIC(18,4),
    "marches_cibles" JSONB,
    "destinations" JSONB,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "offres_entreprise" IS 'Table métier HAUQE Certif';

CREATE TABLE "candidats_doublon" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "entreprise_source_id" UUID NOT NULL,
    "entreprise_cible_id" UUID NOT NULL,
    "criteres_concordants" JSONB,
    "score_similarite" NUMERIC(18,4),
    "statut_examen" VARCHAR(255),
    "decision" VARCHAR(255),
    "motif_decision" VARCHAR(255),
    "examine_par_id" UUID NOT NULL,
    "examine_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "candidats_doublon" IS 'Table métier HAUQE Certif';

CREATE TABLE "organismes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "identifiant_national" VARCHAR(255),
    "nom_officiel" VARCHAR(255),
    "sigle" VARCHAR(255),
    "type_organisme" VARCHAR(255),
    "pays" VARCHAR(255),
    "numero_enregistrement" VARCHAR(255),
    "email" VARCHAR(255),
    "telephone" VARCHAR(255),
    "adresse" TEXT,
    "zone_id" UUID,
    "site_web" VARCHAR(255),
    "statut" VARCHAR(255),
    "date_derniere_verification" DATE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "organismes" IS 'Table métier HAUQE Certif';

CREATE TABLE "accreditations" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "organisme_id" UUID NOT NULL,
    "numero" VARCHAR(255),
    "accrediteur" VARCHAR(255),
    "domaine_technique" VARCHAR(255),
    "perimetre" TEXT,
    "date_delivrance" DATE,
    "date_expiration" DATE,
    "statut" VARCHAR(255),
    "reference_officielle" VARCHAR(255),
    "decision_hauqe" VARCHAR(255),
    "date_decision" DATE,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "accreditations" IS 'Table métier HAUQE Certif';

CREATE TABLE "certifications" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "identifiant_national" VARCHAR(255) NOT NULL,
    "entreprise_id" UUID NOT NULL,
    "organisme_id" UUID NOT NULL,
    "accreditation_id" UUID,
    "norme_id" UUID NOT NULL,
    "numero_certificat" VARCHAR(255),
    "portee" TEXT,
    "date_obtention" DATE,
    "date_effet" DATE,
    "date_expiration" DATE,
    "statut" VARCHAR(255),
    "motif_statut" VARCHAR(255),
    "classification" VARCHAR(255),
    "authenticite_verifiee" BOOLEAN,
    "certification_strategique" BOOLEAN,
    "source_donnee" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "certifications" IS 'Table métier HAUQE Certif';

CREATE TABLE "couvertures_certification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "type_couverture" VARCHAR(255),
    "offre_entreprise_id" UUID,
    "site_entreprise_id" UUID,
    "libelle_couverture" VARCHAR(255),
    "details" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "couvertures_certification" IS 'Table métier HAUQE Certif';

CREATE TABLE "audits_certification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "type_audit" VARCHAR(255),
    "date_prevue" DATE,
    "date_realisee" DATE,
    "auditeur" VARCHAR(255),
    "resultat" TEXT,
    "prochain_audit_at" TIMESTAMPTZ,
    "observations" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "audits_certification" IS 'Table métier HAUQE Certif';

CREATE TABLE "evenements_certification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "type_evenement" VARCHAR(255),
    "ancien_statut" VARCHAR(255),
    "nouveau_statut" VARCHAR(255),
    "date_evenement" TIMESTAMPTZ,
    "motif" TEXT,
    "source" VARCHAR(255),
    "acteur_id" UUID,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "evenements_certification" IS 'Table métier HAUQE Certif';

CREATE TABLE "renouvellements_certification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "date_ouverture" DATE,
    "date_limite" DATE,
    "date_decision" DATE,
    "decision" VARCHAR(255),
    "resultat" TEXT,
    "justification" TEXT,
    "preuves" JSONB,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "renouvellements_certification" IS 'Table métier HAUQE Certif';

CREATE TABLE "documents" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "type_document" VARCHAR(255),
    "nom_original" VARCHAR(255),
    "nom_stockage" VARCHAR(255),
    "chemin_stockage" VARCHAR(255),
    "format" VARCHAR(255),
    "taille_octets" BIGINT,
    "checksum" VARCHAR(255),
    "version" VARCHAR(255),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "confidentialite" VARCHAR(255),
    "source" VARCHAR(255),
    "date_document" DATE,
    "depose_par_id" UUID,
    "date_depot" TIMESTAMPTZ,
    "statut_verification" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "documents" IS 'Table métier HAUQE Certif';

CREATE TABLE "campagnes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "nom" VARCHAR(255),
    "objet" VARCHAR(255),
    "objectif" VARCHAR(255),
    "date_debut" DATE,
    "date_fin" DATE,
    "responsable_id" UUID NOT NULL,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "campagnes" IS 'Table métier HAUQE Certif';

CREATE TABLE "missions_collecte" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "campagne_id" UUID NOT NULL,
    "code" VARCHAR(255),
    "objet" VARCHAR(255),
    "zone_id" UUID NOT NULL,
    "date_debut_prevue" DATE,
    "date_fin_prevue" DATE,
    "date_debut_reelle" DATE,
    "date_fin_reelle" DATE,
    "priorite" VARCHAR(255),
    "progression" INTEGER,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "missions_collecte" IS 'Table métier HAUQE Certif';

CREATE TABLE "affectations_mission" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "mission_id" UUID NOT NULL,
    "utilisateur_id" UUID NOT NULL,
    "role_mission" VARCHAR(255),
    "date_debut" DATE,
    "date_fin" DATE,
    "attribue_par_id" UUID NOT NULL,
    "motif" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "affectations_mission" IS 'Table métier HAUQE Certif';

CREATE TABLE "fiches_collecte" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "mission_id" UUID NOT NULL,
    "entreprise_id" UUID,
    "version_formulaire" VARCHAR(255),
    "numero_revision" INTEGER,
    "statut" VARCHAR(255),
    "taux_completude" NUMERIC(18,4),
    "consentement_obtenu" BOOLEAN,
    "nom_declarant" VARCHAR(255),
    "fonction_declarant" VARCHAR(255),
    "telephone_declarant" VARCHAR(255),
    "email_declarant" VARCHAR(255),
    "signature_declarant" VARCHAR(255),
    "observations" TEXT,
    "collecte_par_id" UUID NOT NULL,
    "collecte_at" TIMESTAMPTZ,
    "soumise_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "fiches_collecte" IS 'Table métier HAUQE Certif';

CREATE TABLE "offres_declarees" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "fiche_collecte_id" UUID NOT NULL,
    "type_offre" VARCHAR(255),
    "nom" VARCHAR(255),
    "description" TEXT,
    "categorie" VARCHAR(255),
    "volume" NUMERIC(18,4),
    "unite" VARCHAR(255),
    "capacite" NUMERIC(18,4),
    "marches_vises" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "offres_declarees" IS 'Table métier HAUQE Certif';

CREATE TABLE "certifications_declarees" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "fiche_collecte_id" UUID NOT NULL,
    "nom_certification" VARCHAR(255),
    "numero" VARCHAR(255),
    "organisme_declare" VARCHAR(255),
    "norme_declaree" VARCHAR(255),
    "portee" TEXT,
    "date_obtention" DATE,
    "date_expiration" DATE,
    "copie_disponible" BOOLEAN,
    "certification_officielle_id" UUID,
    "score_rapprochement" NUMERIC(18,4),
    "statut_rapprochement" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "certifications_declarees" IS 'Table métier HAUQE Certif';

CREATE TABLE "evenements_collecte" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "fiche_collecte_id" UUID NOT NULL,
    "type_evenement" VARCHAR(255),
    "ancien_statut" VARCHAR(255),
    "nouveau_statut" VARCHAR(255),
    "commentaire" TEXT,
    "acteur_id" UUID NOT NULL,
    "date_evenement" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "evenements_collecte" IS 'Table métier HAUQE Certif';

CREATE TABLE "dossiers_verification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "fiche_collecte_id" UUID NOT NULL,
    "date_ouverture" DATE,
    "date_fin" DATE,
    "statut" VARCHAR(255),
    "avis" VARCHAR(255),
    "synthese" TEXT,
    "niveau_risque" VARCHAR(255),
    "priorite" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "dossiers_verification" IS 'Table métier HAUQE Certif';

CREATE TABLE "affectations_verification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_verification_id" UUID NOT NULL,
    "verificateur_id" UUID NOT NULL,
    "date_debut" DATE,
    "date_fin" DATE,
    "date_echeance" DATE,
    "motif" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "affectations_verification" IS 'Table métier HAUQE Certif';

CREATE TABLE "points_verification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_verification_id" UUID NOT NULL,
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "categorie" VARCHAR(255),
    "resultat" TEXT,
    "observation" TEXT,
    "date_verification" DATE,
    "preuve_document_id" UUID,
    "verifie_par_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "points_verification" IS 'Table métier HAUQE Certif';

CREATE TABLE "anomalies_verification" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_verification_id" UUID NOT NULL,
    "point_verification_id" UUID,
    "categorie" VARCHAR(255),
    "gravite" VARCHAR(255),
    "description" TEXT,
    "statut" VARCHAR(255),
    "resolution" TEXT,
    "date_resolution" DATE,
    "escalade" BOOLEAN,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "anomalies_verification" IS 'Table métier HAUQE Certif';

CREATE TABLE "confirmations_externes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_verification_id" UUID NOT NULL,
    "organisme_id" UUID,
    "canal" VARCHAR(255),
    "destinataire" VARCHAR(255),
    "objet" VARCHAR(255),
    "date_envoi" DATE,
    "date_echeance" DATE,
    "date_reponse" DATE,
    "contenu_reponse" TEXT,
    "resultat" TEXT,
    "document_id" UUID,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "confirmations_externes" IS 'Table métier HAUQE Certif';

CREATE TABLE "grilles_fuccs" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "version" VARCHAR(255),
    "date_effet" DATE,
    "date_fin" DATE,
    "reference_approbation" VARCHAR(255),
    "statut_publication" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "grilles_fuccs" IS 'Table métier HAUQE Certif';

CREATE TABLE "rubriques_fuccs" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "grille_fuccs_id" UUID NOT NULL,
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "description" TEXT,
    "ordre_affichage" INTEGER,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "rubriques_fuccs" IS 'Table métier HAUQE Certif';

CREATE TABLE "criteres_fuccs" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "rubrique_fuccs_id" UUID NOT NULL,
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "description" TEXT,
    "score_maximal" NUMERIC(18,4),
    "poids" NUMERIC(18,4),
    "ordre_affichage" INTEGER,
    "commentaire_obligatoire" BOOLEAN,
    "preuve_obligatoire" BOOLEAN,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "criteres_fuccs" IS 'Table métier HAUQE Certif';

CREATE TABLE "controles_fuccs" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_verification_id" UUID NOT NULL,
    "grille_fuccs_id" UUID NOT NULL,
    "controleur_id" UUID NOT NULL,
    "date_debut" DATE,
    "date_fin" DATE,
    "score_brut" NUMERIC(18,4),
    "score_maximal" NUMERIC(18,4),
    "taux" VARCHAR(255),
    "synthese" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "controles_fuccs" IS 'Table métier HAUQE Certif';

CREATE TABLE "notes_criteres" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "controle_fuccs_id" UUID NOT NULL,
    "critere_fuccs_id" UUID NOT NULL,
    "score" NUMERIC(18,4),
    "commentaire" TEXT,
    "preuve_document_id" UUID,
    "note_par_id" UUID NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "notes_criteres" IS 'Table métier HAUQE Certif';

CREATE TABLE "constats_controle" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "controle_fuccs_id" UUID NOT NULL,
    "type_constat" VARCHAR(255),
    "gravite" VARCHAR(255),
    "titre" VARCHAR(255),
    "description" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "constats_controle" IS 'Table métier HAUQE Certif';

CREATE TABLE "validations" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "fiche_collecte_id" UUID NOT NULL,
    "controle_fuccs_id" UUID,
    "niveau_validation" VARCHAR(255),
    "validateur_id" UUID NOT NULL,
    "decision" VARCHAR(255),
    "date_validation" DATE,
    "reserves" VARCHAR(255),
    "justification" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "validations" IS 'Table métier HAUQE Certif';

CREATE TABLE "corrections" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "validation_id" UUID NOT NULL,
    "motif" TEXT,
    "instructions" TEXT,
    "date_demande" DATE,
    "date_echeance" DATE,
    "date_resoumission" DATE,
    "reponse" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "corrections" IS 'Table métier HAUQE Certif';

CREATE TABLE "integrations_bnec" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "validation_id" UUID NOT NULL,
    "administrateur_id" UUID NOT NULL,
    "date_debut" DATE,
    "date_fin" DATE,
    "statut" VARCHAR(255),
    "precontrole" VARCHAR(255),
    "postcontrole" VARCHAR(255),
    "sauvegarde_reference" VARCHAR(255),
    "resume" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "integrations_bnec" IS 'Table métier HAUQE Certif';

CREATE TABLE "elements_integration" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "integration_bnec_id" UUID NOT NULL,
    "type_objet" VARCHAR(255),
    "ressource_source_id" UUID,
    "ressource_cible_id" UUID,
    "revision_source" VARCHAR(255),
    "action" VARCHAR(255),
    "code_genere" VARCHAR(255),
    "statut" VARCHAR(255),
    "message_erreur" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "elements_integration" IS 'Table métier HAUQE Certif';

CREATE TABLE "modeles_scoring" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255),
    "libelle" VARCHAR(255),
    "version" VARCHAR(255),
    "objet_evalue" VARCHAR(255),
    "description" TEXT,
    "date_debut_validite" DATE,
    "date_fin_validite" DATE,
    "regle_calcul" TEXT,
    "reference_approbation" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "modeles_scoring" IS 'Table métier HAUQE Certif';

CREATE TABLE "ponderations_scoring" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "modele_scoring_id" UUID NOT NULL,
    "domaine" VARCHAR(255),
    "valeur" NUMERIC(18,4),
    "periode_debut" VARCHAR(255),
    "periode_fin" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "ponderations_scoring" IS 'Table métier HAUQE Certif';

CREATE TABLE "classifications_entreprise" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "entreprise_id" UUID NOT NULL,
    "modele_scoring_id" UUID NOT NULL,
    "score" NUMERIC(18,4),
    "classe" VARCHAR(255),
    "date_calcul" DATE,
    "date_validation" DATE,
    "sources" JSONB,
    "valide_par_id" UUID NOT NULL,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "classifications_entreprise" IS 'Table métier HAUQE Certif';

CREATE TABLE "resultats_infc" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "modele_scoring_id" UUID NOT NULL,
    "score_global" NUMERIC(18,4),
    "niveau" INTEGER,
    "scores_domaines" JSONB,
    "date_calcul" DATE,
    "date_validation" DATE,
    "sources" JSONB,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "resultats_infc" IS 'Table métier HAUQE Certif';

CREATE TABLE "classements_sncc" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "classe" VARCHAR(255),
    "statut_administratif" VARCHAR(255),
    "niveau_risque" VARCHAR(255),
    "justification" TEXT,
    "date_effet" DATE,
    "date_fin" DATE,
    "valide_par_id" UUID NOT NULL,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "classements_sncc" IS 'Table métier HAUQE Certif';

CREATE TABLE "echeances" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "type_echeance" VARCHAR(255),
    "titre" VARCHAR(255),
    "description" TEXT,
    "date_echeance" DATE,
    "responsable_id" UUID,
    "priorite" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "echeances" IS 'Table métier HAUQE Certif';

CREATE TABLE "alertes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "echeance_id" UUID,
    "type_alerte" VARCHAR(255),
    "niveau" INTEGER,
    "titre" VARCHAR(255),
    "message" TEXT,
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "responsable_id" UUID,
    "date_detection" DATE,
    "date_resolution" DATE,
    "regle_notification" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "alertes" IS 'Table métier HAUQE Certif';

CREATE TABLE "notifications" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "alerte_id" UUID,
    "destinataire_utilisateur_id" UUID,
    "adresse_externe" VARCHAR(255),
    "canal" VARCHAR(255),
    "objet" VARCHAR(255),
    "contenu" TEXT,
    "date_envoi" DATE,
    "date_lecture" DATE,
    "resultat" TEXT,
    "nombre_tentatives" INTEGER,
    "message_erreur" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "notifications" IS 'Table métier HAUQE Certif';

CREATE TABLE "dossiers_veille" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "certification_id" UUID NOT NULL,
    "type_evenement" VARCHAR(255),
    "priorite" VARCHAR(255),
    "date_ouverture" DATE,
    "responsable_id" UUID NOT NULL,
    "prochaine_action_at" TIMESTAMPTZ,
    "date_cloture" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "dossiers_veille" IS 'Table métier HAUQE Certif';

CREATE TABLE "relances_veille" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "dossier_veille_id" UUID NOT NULL,
    "destinataire" VARCHAR(255),
    "canal" VARCHAR(255),
    "objet" VARCHAR(255),
    "date_envoi" DATE,
    "date_echeance" DATE,
    "date_reponse" DATE,
    "reponse" TEXT,
    "resultat" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "relances_veille" IS 'Table métier HAUQE Certif';

CREATE TABLE "rapports_veille" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "type_rapport" VARCHAR(255),
    "periode_debut" VARCHAR(255),
    "periode_fin" VARCHAR(255),
    "nombre_certifications_suivies" INTEGER,
    "nombre_alertes" INTEGER,
    "nombre_renouvellements" INTEGER,
    "delai_moyen_traitement" NUMERIC(18,4),
    "indicateurs" JSONB,
    "prepare_par_id" UUID NOT NULL,
    "valide_par_id" UUID,
    "date_validation" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "rapports_veille" IS 'Table métier HAUQE Certif';

CREATE TABLE "regles_metier" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "famille" VARCHAR(255),
    "libelle" VARCHAR(255),
    "description" TEXT,
    "version" VARCHAR(255),
    "parametres" JSONB,
    "date_debut_effet" DATE,
    "date_fin_effet" DATE,
    "reference_approbation" VARCHAR(255),
    "approuve_par_id" UUID,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "regles_metier" IS 'Table métier HAUQE Certif';

CREATE TABLE "revues_qualite" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "periode_debut" VARCHAR(255),
    "periode_fin" VARCHAR(255),
    "perimetre" TEXT,
    "resultat_global" VARCHAR(255),
    "constats" JSONB,
    "preuves" JSONB,
    "responsable_id" UUID NOT NULL,
    "date_validation" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "revues_qualite" IS 'Table métier HAUQE Certif';

CREATE TABLE "plans_action" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "revue_qualite_id" UUID,
    "titre" VARCHAR(255),
    "objectif" VARCHAR(255),
    "responsable_id" UUID NOT NULL,
    "date_debut" DATE,
    "date_echeance" DATE,
    "priorite" VARCHAR(255),
    "indicateur" VARCHAR(255),
    "progression" INTEGER,
    "date_cloture" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "plans_action" IS 'Table métier HAUQE Certif';

CREATE TABLE "decisions_institutionnelles" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "type_decision" VARCHAR(255),
    "titre" VARCHAR(255),
    "contexte" TEXT,
    "constats" JSONB,
    "risques" VARCHAR(255),
    "options" VARCHAR(255),
    "decision" VARCHAR(255),
    "recommandation" VARCHAR(255),
    "autorite" VARCHAR(255),
    "decide_par_id" UUID,
    "date_decision" DATE,
    "priorite" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "decisions_institutionnelles" IS 'Table métier HAUQE Certif';

CREATE TABLE "publications" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "objet" VARCHAR(255),
    "perimetre" TEXT,
    "niveau_confidentialite" VARCHAR(255),
    "demande_par_id" UUID NOT NULL,
    "date_demande" DATE,
    "decision" VARCHAR(255),
    "autorite_approbation" VARCHAR(255),
    "approuve_par_id" UUID,
    "date_approbation" DATE,
    "reserve" VARCHAR(255),
    "date_publication" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "publications" IS 'Table métier HAUQE Certif';

CREATE TABLE "rapports_generes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code_modele" VARCHAR(255),
    "nom_modele" VARCHAR(255),
    "categorie" VARCHAR(255),
    "demandeur_id" UUID NOT NULL,
    "filtres" JSONB,
    "sections" JSONB,
    "format" VARCHAR(255),
    "periode_debut" VARCHAR(255),
    "periode_fin" VARCHAR(255),
    "date_demande" DATE,
    "date_generation" DATE,
    "document_id" UUID,
    "resultat" TEXT,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "rapports_generes" IS 'Table métier HAUQE Certif';

CREATE TABLE "evenements_audit" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "utilisateur_id" UUID,
    "action" VARCHAR(255),
    "categorie" VARCHAR(255),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "adresse_ip" VARCHAR(255),
    "contexte" TEXT,
    "valeurs_avant" JSONB,
    "valeurs_apres" JSONB,
    "empreinte" VARCHAR(255),
    "resultat" TEXT,
    "date_evenement" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "evenements_audit" IS 'Table métier HAUQE Certif';

CREATE TABLE "archives" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "categorie_donnees" VARCHAR(255),
    "date_archivage" TIMESTAMPTZ,
    "motif" TEXT,
    "auteur_id" UUID NOT NULL,
    "duree_conservation" VARCHAR(255),
    "date_suppression_prevue" DATE,
    "emplacement" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "archives" IS 'Table métier HAUQE Certif';

CREATE TABLE "sauvegardes" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "type_enregistrement" VARCHAR(255),
    "parent_id" UUID,
    "frequence" VARCHAR(255),
    "retention" VARCHAR(255),
    "perimetre" TEXT,
    "emplacement_stockage" VARCHAR(255),
    "date_debut" DATE,
    "date_fin" DATE,
    "taille_octets" BIGINT,
    "integrite_validee" BOOLEAN,
    "resultat" TEXT,
    "preuve_document_id" UUID,
    "message_erreur" VARCHAR(255),
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "sauvegardes" IS 'Table métier HAUQE Certif';

CREATE TABLE "incidents" (
    "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "code" VARCHAR(255) NOT NULL,
    "categorie" VARCHAR(255),
    "gravite" VARCHAR(255),
    "titre" VARCHAR(255),
    "description" TEXT,
    "date_declaration" DATE,
    "declare_par_id" UUID NOT NULL,
    "responsable_id" UUID,
    "ressource_type" VARCHAR(255),
    "ressource_id" UUID,
    "preuves" JSONB,
    "resolution" TEXT,
    "date_resolution" DATE,
    "date_cloture" DATE,
    "statut" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT now(),
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE "incidents" IS 'Table métier HAUQE Certif';

ALTER TABLE "utilisateurs" ADD CONSTRAINT "uq_utilisateurs_email" UNIQUE ("email");
ALTER TABLE "roles" ADD CONSTRAINT "uq_roles_code" UNIQUE ("code");
ALTER TABLE "permissions" ADD CONSTRAINT "uq_permissions_code" UNIQUE ("code");
ALTER TABLE "referentiels" ADD CONSTRAINT "uq_referentiels_code" UNIQUE ("code");
ALTER TABLE "entreprises" ADD CONSTRAINT "uq_entreprises_identifia_ded6f7" UNIQUE ("identifiant_national");
ALTER TABLE "certifications" ADD CONSTRAINT "uq_certifications_identi_62370a" UNIQUE ("identifiant_national");
ALTER TABLE "campagnes" ADD CONSTRAINT "uq_campagnes_code" UNIQUE ("code");
ALTER TABLE "regles_metier" ADD CONSTRAINT "uq_regles_metier_code" UNIQUE ("code");
ALTER TABLE "incidents" ADD CONSTRAINT "uq_incidents_code" UNIQUE ("code");

ALTER TABLE "utilisateurs" ADD CONSTRAINT "fk_utilisateurs_region_a_a3322f" FOREIGN KEY ("region_affectation_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_utilisateurs_region_a_5e066a" ON "utilisateurs" ("region_affectation_id");
ALTER TABLE "utilisateur_role" ADD CONSTRAINT "fk_utilisateur_role_util_8449a1" FOREIGN KEY ("utilisateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_utilisateur_role_util_8a3a25" ON "utilisateur_role" ("utilisateur_id");
ALTER TABLE "utilisateur_role" ADD CONSTRAINT "fk_utilisateur_role_role_id" FOREIGN KEY ("role_id") REFERENCES "roles" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_utilisateur_role_role_id" ON "utilisateur_role" ("role_id");
ALTER TABLE "utilisateur_role" ADD CONSTRAINT "fk_utilisateur_role_attr_67d952" FOREIGN KEY ("attribue_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_utilisateur_role_attr_0893e3" ON "utilisateur_role" ("attribue_par_id");
ALTER TABLE "role_permission" ADD CONSTRAINT "fk_role_permission_role_id" FOREIGN KEY ("role_id") REFERENCES "roles" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_role_permission_role_id" ON "role_permission" ("role_id");
ALTER TABLE "role_permission" ADD CONSTRAINT "fk_role_permission_permi_903320" FOREIGN KEY ("permission_id") REFERENCES "permissions" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_role_permission_permi_17210b" ON "role_permission" ("permission_id");
ALTER TABLE "sessions_utilisateur" ADD CONSTRAINT "fk_sessions_utilisateur_cd289a" FOREIGN KEY ("utilisateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_sessions_utilisateur_cf3b4c" ON "sessions_utilisateur" ("utilisateur_id");
ALTER TABLE "zones_administratives" ADD CONSTRAINT "fk_zones_administratives_4882bf" FOREIGN KEY ("parent_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_zones_administratives_043fd5" ON "zones_administratives" ("parent_id");
ALTER TABLE "valeurs_referentiel" ADD CONSTRAINT "fk_valeurs_referentiel_r_73a827" FOREIGN KEY ("referentiel_id") REFERENCES "referentiels" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_valeurs_referentiel_r_90c1c2" ON "valeurs_referentiel" ("referentiel_id");
ALTER TABLE "valeurs_referentiel" ADD CONSTRAINT "fk_valeurs_referentiel_p_0873df" FOREIGN KEY ("parent_id") REFERENCES "valeurs_referentiel" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_valeurs_referentiel_p_2c72da" ON "valeurs_referentiel" ("parent_id");
ALTER TABLE "entreprises" ADD CONSTRAINT "fk_entreprises_zone_siege_id" FOREIGN KEY ("zone_siege_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_entreprises_zone_siege_id" ON "entreprises" ("zone_siege_id");
ALTER TABLE "contacts_entreprise" ADD CONSTRAINT "fk_contacts_entreprise_e_9794d3" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_contacts_entreprise_e_d78f29" ON "contacts_entreprise" ("entreprise_id");
ALTER TABLE "sites_entreprise" ADD CONSTRAINT "fk_sites_entreprise_entr_4290cf" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_sites_entreprise_entr_3d009e" ON "sites_entreprise" ("entreprise_id");
ALTER TABLE "sites_entreprise" ADD CONSTRAINT "fk_sites_entreprise_zone_id" FOREIGN KEY ("zone_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_sites_entreprise_zone_id" ON "sites_entreprise" ("zone_id");
ALTER TABLE "offres_entreprise" ADD CONSTRAINT "fk_offres_entreprise_ent_09171c" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_offres_entreprise_ent_26be3e" ON "offres_entreprise" ("entreprise_id");
ALTER TABLE "candidats_doublon" ADD CONSTRAINT "fk_candidats_doublon_ent_a5b4a0" FOREIGN KEY ("entreprise_source_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_candidats_doublon_ent_84ea6a" ON "candidats_doublon" ("entreprise_source_id");
ALTER TABLE "candidats_doublon" ADD CONSTRAINT "fk_candidats_doublon_ent_5b3fab" FOREIGN KEY ("entreprise_cible_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_candidats_doublon_ent_3bd287" ON "candidats_doublon" ("entreprise_cible_id");
ALTER TABLE "candidats_doublon" ADD CONSTRAINT "fk_candidats_doublon_exa_b0ab19" FOREIGN KEY ("examine_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_candidats_doublon_exa_7afe67" ON "candidats_doublon" ("examine_par_id");
ALTER TABLE "organismes" ADD CONSTRAINT "fk_organismes_zone_id" FOREIGN KEY ("zone_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_organismes_zone_id" ON "organismes" ("zone_id");
ALTER TABLE "accreditations" ADD CONSTRAINT "fk_accreditations_organisme_id" FOREIGN KEY ("organisme_id") REFERENCES "organismes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_accreditations_organisme_id" ON "accreditations" ("organisme_id");
ALTER TABLE "certifications" ADD CONSTRAINT "fk_certifications_entreprise_id" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_entreprise_id" ON "certifications" ("entreprise_id");
ALTER TABLE "certifications" ADD CONSTRAINT "fk_certifications_organisme_id" FOREIGN KEY ("organisme_id") REFERENCES "organismes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_organisme_id" ON "certifications" ("organisme_id");
ALTER TABLE "certifications" ADD CONSTRAINT "fk_certifications_accred_049b8c" FOREIGN KEY ("accreditation_id") REFERENCES "accreditations" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_accred_b8ffaa" ON "certifications" ("accreditation_id");
ALTER TABLE "certifications" ADD CONSTRAINT "fk_certifications_norme_id" FOREIGN KEY ("norme_id") REFERENCES "normes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_norme_id" ON "certifications" ("norme_id");
ALTER TABLE "couvertures_certification" ADD CONSTRAINT "fk_couvertures_certifica_42dafb" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_couvertures_certifica_e62c03" ON "couvertures_certification" ("certification_id");
ALTER TABLE "couvertures_certification" ADD CONSTRAINT "fk_couvertures_certifica_7b9b67" FOREIGN KEY ("offre_entreprise_id") REFERENCES "offres_entreprise" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_couvertures_certifica_69d68e" ON "couvertures_certification" ("offre_entreprise_id");
ALTER TABLE "couvertures_certification" ADD CONSTRAINT "fk_couvertures_certifica_5dc5a3" FOREIGN KEY ("site_entreprise_id") REFERENCES "sites_entreprise" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_couvertures_certifica_209ef1" ON "couvertures_certification" ("site_entreprise_id");
ALTER TABLE "audits_certification" ADD CONSTRAINT "fk_audits_certification_78365a" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_audits_certification_6e8faa" ON "audits_certification" ("certification_id");
ALTER TABLE "evenements_certification" ADD CONSTRAINT "fk_evenements_certificat_241167" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_evenements_certificat_21178e" ON "evenements_certification" ("certification_id");
ALTER TABLE "evenements_certification" ADD CONSTRAINT "fk_evenements_certificat_287133" FOREIGN KEY ("acteur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_evenements_certificat_2ea2d9" ON "evenements_certification" ("acteur_id");
ALTER TABLE "renouvellements_certification" ADD CONSTRAINT "fk_renouvellements_certi_86bb42" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_renouvellements_certi_5ab3b8" ON "renouvellements_certification" ("certification_id");
ALTER TABLE "documents" ADD CONSTRAINT "fk_documents_depose_par_id" FOREIGN KEY ("depose_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_documents_depose_par_id" ON "documents" ("depose_par_id");
ALTER TABLE "campagnes" ADD CONSTRAINT "fk_campagnes_responsable_id" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_campagnes_responsable_id" ON "campagnes" ("responsable_id");
ALTER TABLE "missions_collecte" ADD CONSTRAINT "fk_missions_collecte_cam_e3652f" FOREIGN KEY ("campagne_id") REFERENCES "campagnes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_missions_collecte_cam_da6858" ON "missions_collecte" ("campagne_id");
ALTER TABLE "missions_collecte" ADD CONSTRAINT "fk_missions_collecte_zone_id" FOREIGN KEY ("zone_id") REFERENCES "zones_administratives" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_missions_collecte_zone_id" ON "missions_collecte" ("zone_id");
ALTER TABLE "affectations_mission" ADD CONSTRAINT "fk_affectations_mission_3a427e" FOREIGN KEY ("mission_id") REFERENCES "missions_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_affectations_mission_e9c5a3" ON "affectations_mission" ("mission_id");
ALTER TABLE "affectations_mission" ADD CONSTRAINT "fk_affectations_mission_ec27bf" FOREIGN KEY ("utilisateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_affectations_mission_9f9b13" ON "affectations_mission" ("utilisateur_id");
ALTER TABLE "affectations_mission" ADD CONSTRAINT "fk_affectations_mission_744bbb" FOREIGN KEY ("attribue_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_affectations_mission_d1d47d" ON "affectations_mission" ("attribue_par_id");
ALTER TABLE "fiches_collecte" ADD CONSTRAINT "fk_fiches_collecte_mission_id" FOREIGN KEY ("mission_id") REFERENCES "missions_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_fiches_collecte_mission_id" ON "fiches_collecte" ("mission_id");
ALTER TABLE "fiches_collecte" ADD CONSTRAINT "fk_fiches_collecte_entre_68a704" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_fiches_collecte_entre_14b9be" ON "fiches_collecte" ("entreprise_id");
ALTER TABLE "fiches_collecte" ADD CONSTRAINT "fk_fiches_collecte_colle_389d2e" FOREIGN KEY ("collecte_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_fiches_collecte_colle_5b918e" ON "fiches_collecte" ("collecte_par_id");
ALTER TABLE "offres_declarees" ADD CONSTRAINT "fk_offres_declarees_fich_56b203" FOREIGN KEY ("fiche_collecte_id") REFERENCES "fiches_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_offres_declarees_fich_2986d0" ON "offres_declarees" ("fiche_collecte_id");
ALTER TABLE "certifications_declarees" ADD CONSTRAINT "fk_certifications_declar_48b290" FOREIGN KEY ("fiche_collecte_id") REFERENCES "fiches_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_declar_ef89a1" ON "certifications_declarees" ("fiche_collecte_id");
ALTER TABLE "certifications_declarees" ADD CONSTRAINT "fk_certifications_declar_63d0b5" FOREIGN KEY ("certification_officielle_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_certifications_declar_10db9a" ON "certifications_declarees" ("certification_officielle_id");
ALTER TABLE "evenements_collecte" ADD CONSTRAINT "fk_evenements_collecte_f_f779ec" FOREIGN KEY ("fiche_collecte_id") REFERENCES "fiches_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_evenements_collecte_f_134915" ON "evenements_collecte" ("fiche_collecte_id");
ALTER TABLE "evenements_collecte" ADD CONSTRAINT "fk_evenements_collecte_a_ae4021" FOREIGN KEY ("acteur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_evenements_collecte_a_eaa86b" ON "evenements_collecte" ("acteur_id");
ALTER TABLE "dossiers_verification" ADD CONSTRAINT "fk_dossiers_verification_7ef699" FOREIGN KEY ("fiche_collecte_id") REFERENCES "fiches_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_dossiers_verification_422f77" ON "dossiers_verification" ("fiche_collecte_id");
ALTER TABLE "affectations_verification" ADD CONSTRAINT "fk_affectations_verifica_e99b9e" FOREIGN KEY ("dossier_verification_id") REFERENCES "dossiers_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_affectations_verifica_516e19" ON "affectations_verification" ("dossier_verification_id");
ALTER TABLE "affectations_verification" ADD CONSTRAINT "fk_affectations_verifica_7faed5" FOREIGN KEY ("verificateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_affectations_verifica_924ca3" ON "affectations_verification" ("verificateur_id");
ALTER TABLE "points_verification" ADD CONSTRAINT "fk_points_verification_d_4e971d" FOREIGN KEY ("dossier_verification_id") REFERENCES "dossiers_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_points_verification_d_bc5b8f" ON "points_verification" ("dossier_verification_id");
ALTER TABLE "points_verification" ADD CONSTRAINT "fk_points_verification_p_403d71" FOREIGN KEY ("preuve_document_id") REFERENCES "documents" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_points_verification_p_98b674" ON "points_verification" ("preuve_document_id");
ALTER TABLE "points_verification" ADD CONSTRAINT "fk_points_verification_v_23c7a7" FOREIGN KEY ("verifie_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_points_verification_v_abcf9b" ON "points_verification" ("verifie_par_id");
ALTER TABLE "anomalies_verification" ADD CONSTRAINT "fk_anomalies_verificatio_ab8555" FOREIGN KEY ("dossier_verification_id") REFERENCES "dossiers_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_anomalies_verificatio_930aaa" ON "anomalies_verification" ("dossier_verification_id");
ALTER TABLE "anomalies_verification" ADD CONSTRAINT "fk_anomalies_verificatio_254467" FOREIGN KEY ("point_verification_id") REFERENCES "points_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_anomalies_verificatio_63b226" ON "anomalies_verification" ("point_verification_id");
ALTER TABLE "confirmations_externes" ADD CONSTRAINT "fk_confirmations_externe_d05ff9" FOREIGN KEY ("dossier_verification_id") REFERENCES "dossiers_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_confirmations_externe_4f2bcc" ON "confirmations_externes" ("dossier_verification_id");
ALTER TABLE "confirmations_externes" ADD CONSTRAINT "fk_confirmations_externe_3085b9" FOREIGN KEY ("organisme_id") REFERENCES "organismes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_confirmations_externe_d8e20e" ON "confirmations_externes" ("organisme_id");
ALTER TABLE "confirmations_externes" ADD CONSTRAINT "fk_confirmations_externe_7ad1b0" FOREIGN KEY ("document_id") REFERENCES "documents" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_confirmations_externe_637d51" ON "confirmations_externes" ("document_id");
ALTER TABLE "rubriques_fuccs" ADD CONSTRAINT "fk_rubriques_fuccs_grill_08b65b" FOREIGN KEY ("grille_fuccs_id") REFERENCES "grilles_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_rubriques_fuccs_grill_95c60c" ON "rubriques_fuccs" ("grille_fuccs_id");
ALTER TABLE "criteres_fuccs" ADD CONSTRAINT "fk_criteres_fuccs_rubriq_a865d5" FOREIGN KEY ("rubrique_fuccs_id") REFERENCES "rubriques_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_criteres_fuccs_rubriq_7d6e17" ON "criteres_fuccs" ("rubrique_fuccs_id");
ALTER TABLE "controles_fuccs" ADD CONSTRAINT "fk_controles_fuccs_dossi_5c3a2e" FOREIGN KEY ("dossier_verification_id") REFERENCES "dossiers_verification" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_controles_fuccs_dossi_1a70b5" ON "controles_fuccs" ("dossier_verification_id");
ALTER TABLE "controles_fuccs" ADD CONSTRAINT "fk_controles_fuccs_grill_889fa4" FOREIGN KEY ("grille_fuccs_id") REFERENCES "grilles_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_controles_fuccs_grill_24c31d" ON "controles_fuccs" ("grille_fuccs_id");
ALTER TABLE "controles_fuccs" ADD CONSTRAINT "fk_controles_fuccs_contr_728db8" FOREIGN KEY ("controleur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_controles_fuccs_contr_4fad86" ON "controles_fuccs" ("controleur_id");
ALTER TABLE "notes_criteres" ADD CONSTRAINT "fk_notes_criteres_contro_6126e6" FOREIGN KEY ("controle_fuccs_id") REFERENCES "controles_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notes_criteres_contro_a61cd4" ON "notes_criteres" ("controle_fuccs_id");
ALTER TABLE "notes_criteres" ADD CONSTRAINT "fk_notes_criteres_criter_f23d76" FOREIGN KEY ("critere_fuccs_id") REFERENCES "criteres_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notes_criteres_criter_b48064" ON "notes_criteres" ("critere_fuccs_id");
ALTER TABLE "notes_criteres" ADD CONSTRAINT "fk_notes_criteres_preuve_7c6f25" FOREIGN KEY ("preuve_document_id") REFERENCES "documents" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notes_criteres_preuve_3dcd86" ON "notes_criteres" ("preuve_document_id");
ALTER TABLE "notes_criteres" ADD CONSTRAINT "fk_notes_criteres_note_par_id" FOREIGN KEY ("note_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notes_criteres_note_par_id" ON "notes_criteres" ("note_par_id");
ALTER TABLE "constats_controle" ADD CONSTRAINT "fk_constats_controle_con_71bdbb" FOREIGN KEY ("controle_fuccs_id") REFERENCES "controles_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_constats_controle_con_75b92d" ON "constats_controle" ("controle_fuccs_id");
ALTER TABLE "validations" ADD CONSTRAINT "fk_validations_fiche_col_3d1583" FOREIGN KEY ("fiche_collecte_id") REFERENCES "fiches_collecte" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_validations_fiche_col_81ca76" ON "validations" ("fiche_collecte_id");
ALTER TABLE "validations" ADD CONSTRAINT "fk_validations_controle_fa523f" FOREIGN KEY ("controle_fuccs_id") REFERENCES "controles_fuccs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_validations_controle_3fa0ee" ON "validations" ("controle_fuccs_id");
ALTER TABLE "validations" ADD CONSTRAINT "fk_validations_validateur_id" FOREIGN KEY ("validateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_validations_validateur_id" ON "validations" ("validateur_id");
ALTER TABLE "corrections" ADD CONSTRAINT "fk_corrections_validation_id" FOREIGN KEY ("validation_id") REFERENCES "validations" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_corrections_validation_id" ON "corrections" ("validation_id");
ALTER TABLE "integrations_bnec" ADD CONSTRAINT "fk_integrations_bnec_val_09e9d5" FOREIGN KEY ("validation_id") REFERENCES "validations" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_integrations_bnec_val_8db6a7" ON "integrations_bnec" ("validation_id");
ALTER TABLE "integrations_bnec" ADD CONSTRAINT "fk_integrations_bnec_adm_29c5b5" FOREIGN KEY ("administrateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_integrations_bnec_adm_5976cb" ON "integrations_bnec" ("administrateur_id");
ALTER TABLE "elements_integration" ADD CONSTRAINT "fk_elements_integration_3b4d4e" FOREIGN KEY ("integration_bnec_id") REFERENCES "integrations_bnec" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_elements_integration_be480c" ON "elements_integration" ("integration_bnec_id");
ALTER TABLE "ponderations_scoring" ADD CONSTRAINT "fk_ponderations_scoring_0c6f93" FOREIGN KEY ("modele_scoring_id") REFERENCES "modeles_scoring" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_ponderations_scoring_8ec8e9" ON "ponderations_scoring" ("modele_scoring_id");
ALTER TABLE "classifications_entreprise" ADD CONSTRAINT "fk_classifications_entre_acbb95" FOREIGN KEY ("entreprise_id") REFERENCES "entreprises" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_classifications_entre_5240d8" ON "classifications_entreprise" ("entreprise_id");
ALTER TABLE "classifications_entreprise" ADD CONSTRAINT "fk_classifications_entre_c1b3dc" FOREIGN KEY ("modele_scoring_id") REFERENCES "modeles_scoring" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_classifications_entre_18efb6" ON "classifications_entreprise" ("modele_scoring_id");
ALTER TABLE "classifications_entreprise" ADD CONSTRAINT "fk_classifications_entre_24a33c" FOREIGN KEY ("valide_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_classifications_entre_7d018f" ON "classifications_entreprise" ("valide_par_id");
ALTER TABLE "resultats_infc" ADD CONSTRAINT "fk_resultats_infc_certif_399a4b" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_resultats_infc_certif_1904c4" ON "resultats_infc" ("certification_id");
ALTER TABLE "resultats_infc" ADD CONSTRAINT "fk_resultats_infc_modele_dd0622" FOREIGN KEY ("modele_scoring_id") REFERENCES "modeles_scoring" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_resultats_infc_modele_f25427" ON "resultats_infc" ("modele_scoring_id");
ALTER TABLE "classements_sncc" ADD CONSTRAINT "fk_classements_sncc_cert_cdd1b9" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_classements_sncc_cert_44e587" ON "classements_sncc" ("certification_id");
ALTER TABLE "classements_sncc" ADD CONSTRAINT "fk_classements_sncc_vali_6bd278" FOREIGN KEY ("valide_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_classements_sncc_vali_48f402" ON "classements_sncc" ("valide_par_id");
ALTER TABLE "echeances" ADD CONSTRAINT "fk_echeances_responsable_id" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_echeances_responsable_id" ON "echeances" ("responsable_id");
ALTER TABLE "alertes" ADD CONSTRAINT "fk_alertes_echeance_id" FOREIGN KEY ("echeance_id") REFERENCES "echeances" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_alertes_echeance_id" ON "alertes" ("echeance_id");
ALTER TABLE "alertes" ADD CONSTRAINT "fk_alertes_responsable_id" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_alertes_responsable_id" ON "alertes" ("responsable_id");
ALTER TABLE "notifications" ADD CONSTRAINT "fk_notifications_alerte_id" FOREIGN KEY ("alerte_id") REFERENCES "alertes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notifications_alerte_id" ON "notifications" ("alerte_id");
ALTER TABLE "notifications" ADD CONSTRAINT "fk_notifications_destina_674fe4" FOREIGN KEY ("destinataire_utilisateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_notifications_destina_cc9fd6" ON "notifications" ("destinataire_utilisateur_id");
ALTER TABLE "dossiers_veille" ADD CONSTRAINT "fk_dossiers_veille_certi_b9734d" FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_dossiers_veille_certi_19678a" ON "dossiers_veille" ("certification_id");
ALTER TABLE "dossiers_veille" ADD CONSTRAINT "fk_dossiers_veille_respo_757606" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_dossiers_veille_respo_67e064" ON "dossiers_veille" ("responsable_id");
ALTER TABLE "relances_veille" ADD CONSTRAINT "fk_relances_veille_dossi_f0e01d" FOREIGN KEY ("dossier_veille_id") REFERENCES "dossiers_veille" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_relances_veille_dossi_419739" ON "relances_veille" ("dossier_veille_id");
ALTER TABLE "rapports_veille" ADD CONSTRAINT "fk_rapports_veille_prepa_9524fb" FOREIGN KEY ("prepare_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_rapports_veille_prepa_c181dd" ON "rapports_veille" ("prepare_par_id");
ALTER TABLE "rapports_veille" ADD CONSTRAINT "fk_rapports_veille_valid_0f8014" FOREIGN KEY ("valide_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_rapports_veille_valid_585722" ON "rapports_veille" ("valide_par_id");
ALTER TABLE "regles_metier" ADD CONSTRAINT "fk_regles_metier_approuv_9f1a56" FOREIGN KEY ("approuve_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_regles_metier_approuv_131b24" ON "regles_metier" ("approuve_par_id");
ALTER TABLE "revues_qualite" ADD CONSTRAINT "fk_revues_qualite_respon_41290e" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_revues_qualite_respon_c8951e" ON "revues_qualite" ("responsable_id");
ALTER TABLE "plans_action" ADD CONSTRAINT "fk_plans_action_revue_qu_09278c" FOREIGN KEY ("revue_qualite_id") REFERENCES "revues_qualite" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_plans_action_revue_qu_c573cb" ON "plans_action" ("revue_qualite_id");
ALTER TABLE "plans_action" ADD CONSTRAINT "fk_plans_action_responsable_id" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_plans_action_responsable_id" ON "plans_action" ("responsable_id");
ALTER TABLE "decisions_institutionnelles" ADD CONSTRAINT "fk_decisions_institution_1f17c3" FOREIGN KEY ("decide_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_decisions_institution_843032" ON "decisions_institutionnelles" ("decide_par_id");
ALTER TABLE "publications" ADD CONSTRAINT "fk_publications_demande_par_id" FOREIGN KEY ("demande_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_publications_demande_par_id" ON "publications" ("demande_par_id");
ALTER TABLE "publications" ADD CONSTRAINT "fk_publications_approuve_par_id" FOREIGN KEY ("approuve_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_publications_approuve_par_id" ON "publications" ("approuve_par_id");
ALTER TABLE "rapports_generes" ADD CONSTRAINT "fk_rapports_generes_dema_f7ac5b" FOREIGN KEY ("demandeur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_rapports_generes_dema_c08e10" ON "rapports_generes" ("demandeur_id");
ALTER TABLE "rapports_generes" ADD CONSTRAINT "fk_rapports_generes_document_id" FOREIGN KEY ("document_id") REFERENCES "documents" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_rapports_generes_document_id" ON "rapports_generes" ("document_id");
ALTER TABLE "evenements_audit" ADD CONSTRAINT "fk_evenements_audit_util_7e4521" FOREIGN KEY ("utilisateur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_evenements_audit_util_92560f" ON "evenements_audit" ("utilisateur_id");
ALTER TABLE "archives" ADD CONSTRAINT "fk_archives_auteur_id" FOREIGN KEY ("auteur_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_archives_auteur_id" ON "archives" ("auteur_id");
ALTER TABLE "sauvegardes" ADD CONSTRAINT "fk_sauvegardes_parent_id" FOREIGN KEY ("parent_id") REFERENCES "sauvegardes" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_sauvegardes_parent_id" ON "sauvegardes" ("parent_id");
ALTER TABLE "sauvegardes" ADD CONSTRAINT "fk_sauvegardes_preuve_do_821598" FOREIGN KEY ("preuve_document_id") REFERENCES "documents" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_sauvegardes_preuve_do_117e5c" ON "sauvegardes" ("preuve_document_id");
ALTER TABLE "incidents" ADD CONSTRAINT "fk_incidents_declare_par_id" FOREIGN KEY ("declare_par_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_incidents_declare_par_id" ON "incidents" ("declare_par_id");
ALTER TABLE "incidents" ADD CONSTRAINT "fk_incidents_responsable_id" FOREIGN KEY ("responsable_id") REFERENCES "utilisateurs" ("id") ON UPDATE CASCADE ON DELETE RESTRICT;
CREATE INDEX "ix_incidents_responsable_id" ON "incidents" ("responsable_id");
CREATE INDEX "ix_roles_code" ON "roles" ("code");
CREATE INDEX "ix_permissions_code" ON "permissions" ("code");
CREATE INDEX "ix_referentiels_code" ON "referentiels" ("code");
CREATE INDEX "ix_normes_code" ON "normes" ("code");
CREATE INDEX "ix_grilles_fuccs_code" ON "grilles_fuccs" ("code");
CREATE INDEX "ix_modeles_scoring_code" ON "modeles_scoring" ("code");

-- Mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER "trg_utilisateurs_upd" BEFORE UPDATE ON "utilisateurs" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_roles_upd" BEFORE UPDATE ON "roles" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_permissions_upd" BEFORE UPDATE ON "permissions" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_utilisateur_role_upd" BEFORE UPDATE ON "utilisateur_role" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_role_permission_upd" BEFORE UPDATE ON "role_permission" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_sessions_utilisateur_upd" BEFORE UPDATE ON "sessions_utilisateur" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_zones_administrat_d836c3" BEFORE UPDATE ON "zones_administratives" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_referentiels_upd" BEFORE UPDATE ON "referentiels" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_valeurs_referentiel_upd" BEFORE UPDATE ON "valeurs_referentiel" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_normes_upd" BEFORE UPDATE ON "normes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_entreprises_upd" BEFORE UPDATE ON "entreprises" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_contacts_entreprise_upd" BEFORE UPDATE ON "contacts_entreprise" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_sites_entreprise_upd" BEFORE UPDATE ON "sites_entreprise" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_offres_entreprise_upd" BEFORE UPDATE ON "offres_entreprise" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_candidats_doublon_upd" BEFORE UPDATE ON "candidats_doublon" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_organismes_upd" BEFORE UPDATE ON "organismes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_accreditations_upd" BEFORE UPDATE ON "accreditations" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_certifications_upd" BEFORE UPDATE ON "certifications" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_couvertures_certi_981364" BEFORE UPDATE ON "couvertures_certification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_audits_certification_upd" BEFORE UPDATE ON "audits_certification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_evenements_certif_e9a4b9" BEFORE UPDATE ON "evenements_certification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_renouvellements_c_a8324e" BEFORE UPDATE ON "renouvellements_certification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_documents_upd" BEFORE UPDATE ON "documents" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_campagnes_upd" BEFORE UPDATE ON "campagnes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_missions_collecte_upd" BEFORE UPDATE ON "missions_collecte" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_affectations_mission_upd" BEFORE UPDATE ON "affectations_mission" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_fiches_collecte_upd" BEFORE UPDATE ON "fiches_collecte" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_offres_declarees_upd" BEFORE UPDATE ON "offres_declarees" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_certifications_de_df0ffc" BEFORE UPDATE ON "certifications_declarees" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_evenements_collecte_upd" BEFORE UPDATE ON "evenements_collecte" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_dossiers_verifica_74ad2c" BEFORE UPDATE ON "dossiers_verification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_affectations_veri_ca5a79" BEFORE UPDATE ON "affectations_verification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_points_verification_upd" BEFORE UPDATE ON "points_verification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_anomalies_verific_ed3828" BEFORE UPDATE ON "anomalies_verification" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_confirmations_ext_944e23" BEFORE UPDATE ON "confirmations_externes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_grilles_fuccs_upd" BEFORE UPDATE ON "grilles_fuccs" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_rubriques_fuccs_upd" BEFORE UPDATE ON "rubriques_fuccs" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_criteres_fuccs_upd" BEFORE UPDATE ON "criteres_fuccs" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_controles_fuccs_upd" BEFORE UPDATE ON "controles_fuccs" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_notes_criteres_upd" BEFORE UPDATE ON "notes_criteres" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_constats_controle_upd" BEFORE UPDATE ON "constats_controle" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_validations_upd" BEFORE UPDATE ON "validations" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_corrections_upd" BEFORE UPDATE ON "corrections" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_integrations_bnec_upd" BEFORE UPDATE ON "integrations_bnec" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_elements_integration_upd" BEFORE UPDATE ON "elements_integration" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_modeles_scoring_upd" BEFORE UPDATE ON "modeles_scoring" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_ponderations_scoring_upd" BEFORE UPDATE ON "ponderations_scoring" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_classifications_e_4daa79" BEFORE UPDATE ON "classifications_entreprise" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_resultats_infc_upd" BEFORE UPDATE ON "resultats_infc" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_classements_sncc_upd" BEFORE UPDATE ON "classements_sncc" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_echeances_upd" BEFORE UPDATE ON "echeances" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_alertes_upd" BEFORE UPDATE ON "alertes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_notifications_upd" BEFORE UPDATE ON "notifications" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_dossiers_veille_upd" BEFORE UPDATE ON "dossiers_veille" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_relances_veille_upd" BEFORE UPDATE ON "relances_veille" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_rapports_veille_upd" BEFORE UPDATE ON "rapports_veille" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_regles_metier_upd" BEFORE UPDATE ON "regles_metier" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_revues_qualite_upd" BEFORE UPDATE ON "revues_qualite" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_plans_action_upd" BEFORE UPDATE ON "plans_action" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_decisions_institu_b334dc" BEFORE UPDATE ON "decisions_institutionnelles" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_publications_upd" BEFORE UPDATE ON "publications" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_rapports_generes_upd" BEFORE UPDATE ON "rapports_generes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_evenements_audit_upd" BEFORE UPDATE ON "evenements_audit" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_archives_upd" BEFORE UPDATE ON "archives" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_sauvegardes_upd" BEFORE UPDATE ON "sauvegardes" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER "trg_incidents_upd" BEFORE UPDATE ON "incidents" FOR EACH ROW EXECUTE FUNCTION set_updated_at();
