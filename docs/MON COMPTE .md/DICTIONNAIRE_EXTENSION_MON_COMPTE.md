# Dictionnaire d'extension — Mon compte / Sécurité

Cette annexe complète le dictionnaire initial **66 tables / 843 colonnes**.

Après migration `c5b7a8f2d901` :

```text
Tables métier : 70
Nouvelles tables : 4
```

## 67. `preferences_utilisateur`

| Colonne | Type | Contraintes |
|---|---|---|
| id | UUID | PK |
| utilisateur_id | UUID | FK utilisateurs, UNIQUE, NN |
| langue | VARCHAR(20) | NN, défaut fr |
| fuseau_horaire | VARCHAR(100) | NN, défaut Africa/Lome |
| avatar_document_id | UUID | FK documents, facultatif |
| notifications_alertes_critiques | BOOLEAN | NN |
| notifications_affectations | BOOLEAN | NN |
| notifications_corrections | BOOLEAN | NN |
| notifications_rapports_planifies | BOOLEAN | NN |
| notifications_resume_hebdomadaire | BOOLEAN | NN |
| created_at | TIMESTAMPTZ | NN |
| updated_at | TIMESTAMPTZ | NN |

## 68. `securite_compte_utilisateur`

| Colonne | Type | Contraintes |
|---|---|---|
| id | UUID | PK |
| utilisateur_id | UUID | FK utilisateurs, UNIQUE, NN |
| mfa_type | VARCHAR(30) | NN |
| mfa_secret_chiffre | TEXT | secret TOTP chiffré |
| mfa_secret_pending_chiffre | TEXT | enrôlement en attente |
| mfa_recovery_codes_hash | JSONB | hashes Argon2 |
| mfa_verifie_at | TIMESTAMPTZ | facultatif |
| code_prive_hash | VARCHAR(255) | Argon2 |
| verrouillage_auto_active | BOOLEAN | NN |
| delai_verrouillage_minutes | INTEGER | 5/10/15/30 |
| code_prive_configure_at | TIMESTAMPTZ | facultatif |
| inactivite_warning_sent_at | TIMESTAMPTZ | RM-33 |
| reactivation_at | TIMESTAMPTZ | grâce après réactivation admin |
| derniere_modification_mot_de_passe_at | TIMESTAMPTZ | facultatif |
| created_at | TIMESTAMPTZ | NN |
| updated_at | TIMESTAMPTZ | NN |

## 69. `verrous_session_utilisateur`

| Colonne | Type | Contraintes |
|---|---|---|
| id | UUID | PK |
| session_utilisateur_id | UUID | FK sessions_utilisateur, UNIQUE, NN |
| verrouillee_at | TIMESTAMPTZ | facultatif |
| deverrouillee_at | TIMESTAMPTZ | facultatif |
| tentatives_code_prive | INTEGER | NN, défaut 0 |
| derniere_tentative_at | TIMESTAMPTZ | facultatif |
| motif | VARCHAR(255) | facultatif |
| created_at | TIMESTAMPTZ | NN |
| updated_at | TIMESTAMPTZ | NN |

## 70. `jetons_securite_utilisateur`

| Colonne | Type | Contraintes |
|---|---|---|
| id | UUID | PK |
| utilisateur_id | UUID | FK utilisateurs, NN |
| type_jeton | VARCHAR(50) | NN |
| jeton_hash | VARCHAR(64) | UNIQUE, NN |
| expiration_at | TIMESTAMPTZ | NN |
| utilise_at | TIMESTAMPTZ | facultatif |
| adresse_ip | VARCHAR(255) | facultatif |
| user_agent | VARCHAR(255) | facultatif |
| contexte | JSONB | facultatif |
| created_at | TIMESTAMPTZ | NN |
| updated_at | TIMESTAMPTZ | NN |
