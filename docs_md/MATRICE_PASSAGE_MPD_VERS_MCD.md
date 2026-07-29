# Matrice de passage du MPD vers le MCD — HAUQE Certif

**Source contrôlée :** `output\Livrable v01\MPD_HAUQE_CERTIF_V01.pdm`  
**Tables MPD :** 66  
**Objectif :** transformer le modèle physique en modèle conceptuel lisible pour le livrable contractuel.

| N° | Table du MPD | Colonnes | Traitement MCD | Objet conceptuel cible | Décision |
|---:|---|---:|---|---|---|
| 1 | `utilisateurs` | 13 | ENTITÉ | Utilisateur | Conserver les attributs métier, masquer les champs d’audit. |
| 2 | `roles` | 8 | ENTITÉ | Rôle | Conserver. |
| 3 | `permissions` | 7 | ENTITÉ | Permission | Conserver dans le MCD détaillé. |
| 4 | `utilisateur_role` | 10 | ASSOCIATION | Attribuer un rôle | Transformer la table de liaison en association porteuse de dates et motif. |
| 5 | `role_permission` | 5 | ASSOCIATION | Autoriser | Transformer en association Rôle–Permission. |
| 6 | `sessions_utilisateur` | 11 | TECHNIQUE | — | Masquer du MCD ; conserver uniquement dans le MPD. |
| 7 | `zones_administratives` | 10 | ENTITÉ | Zone administrative | Conserver la hiérarchie récursive. |
| 8 | `referentiels` | 8 | ENTITÉ | Référentiel | Conserver dans le MCD détaillé. |
| 9 | `valeurs_referentiel` | 12 | ENTITÉ | Valeur de référentiel | Conserver et relier au référentiel. |
| 10 | `normes` | 13 | ENTITÉ | Norme | Conserver. |
| 11 | `entreprises` | 26 | ENTITÉ | Entreprise | Entité centrale. |
| 12 | `contacts_entreprise` | 12 | ENTITÉ | Contact d’entreprise | Conserver, cardinalité multiple. |
| 13 | `sites_entreprise` | 13 | ENTITÉ | Site d’entreprise | Conserver, cardinalité multiple. |
| 14 | `offres_entreprise` | 14 | ENTITÉ | Offre d’entreprise | Produit ou service proposé. |
| 15 | `candidats_doublon` | 12 | FUSION | Contrôle de doublon | Présenter comme résultat de contrôle, pas comme entité centrale. |
| 16 | `organismes` | 16 | ENTITÉ | Organisme | Conserver. |
| 17 | `accreditations` | 14 | ENTITÉ | Accréditation | Conserver. |
| 18 | `certifications` | 19 | ENTITÉ | Certification | Entité centrale. |
| 19 | `couvertures_certification` | 10 | ASSOCIATION | Couvrir | Association porteuse entre Certification et Offre/Site. |
| 20 | `audits_certification` | 12 | ENTITÉ | Audit de certification | Conserver. |
| 21 | `evenements_certification` | 11 | HISTORIQUE | Historique de certification | Masquer du contracté ; conserver comme historique dans le détaillé. |
| 22 | `renouvellements_certification` | 12 | ENTITÉ | Renouvellement | Conserver. |
| 23 | `documents` | 20 | ENTITÉ | Document | Conserver comme preuve documentaire transverse. |
| 24 | `campagnes` | 11 | ENTITÉ | Campagne | Conserver. |
| 25 | `missions_collecte` | 14 | ENTITÉ | Mission de collecte | Conserver. |
| 26 | `affectations_mission` | 11 | ASSOCIATION | Affecter à une mission | Association Utilisateur–Mission avec dates et rôle. |
| 27 | `fiches_collecte` | 19 | ENTITÉ | Fiche de collecte | Conserver. |
| 28 | `offres_declarees` | 13 | ENTITÉ | Offre déclarée | Séparer des données officielles. |
| 29 | `certifications_declarees` | 15 | ENTITÉ | Certification déclarée | Séparer des certifications officielles. |
| 30 | `evenements_collecte` | 10 | HISTORIQUE | Historique de collecte | Masquer du contracté ; conserver dans le détaillé. |
| 31 | `dossiers_verification` | 11 | ENTITÉ | Dossier de vérification | Conserver. |
| 32 | `affectations_verification` | 10 | ASSOCIATION | Affecter à la vérification | Association Utilisateur–Dossier. |
| 33 | `points_verification` | 12 | ENTITÉ | Point de vérification | Conserver. |
| 34 | `anomalies_verification` | 12 | ENTITÉ | Anomalie de vérification | Conserver. |
| 35 | `confirmations_externes` | 15 | ENTITÉ | Confirmation externe | Conserver. |
| 36 | `grilles_fuccs` | 10 | ENTITÉ | Grille FUCCS | Conserver. |
| 37 | `rubriques_fuccs` | 8 | ENTITÉ | Rubrique FUCCS | Conserver. |
| 38 | `criteres_fuccs` | 12 | ENTITÉ | Critère FUCCS | Conserver. |
| 39 | `controles_fuccs` | 13 | ENTITÉ | Contrôle FUCCS | Conserver. |
| 40 | `notes_criteres` | 9 | ASSOCIATION | Évaluer un critère | Association Contrôle–Critère porteuse du score et de la preuve. |
| 41 | `constats_controle` | 9 | ENTITÉ | Constat de contrôle | Conserver. |
| 42 | `validations` | 12 | ENTITÉ | Validation | Conserver. |
| 43 | `corrections` | 11 | ENTITÉ | Correction | Conserver. |
| 44 | `integrations_bnec` | 12 | ENTITÉ | Intégration BNEC | Conserver. |
| 45 | `elements_integration` | 12 | FUSION | Élément intégré | Présenter comme détail de l’intégration, pas dans le contracté. |
| 46 | `modeles_scoring` | 13 | ENTITÉ | Modèle de scoring | Conserver. |
| 47 | `ponderations_scoring` | 9 | ASSOCIATION | Pondérer un domaine | Association porteuse rattachée au modèle de scoring. |
| 48 | `classifications_entreprise` | 12 | ENTITÉ | Classification d’entreprise | Conserver. |
| 49 | `resultats_infc` | 12 | ENTITÉ | Résultat INFC | Conserver. |
| 50 | `classements_sncc` | 12 | ENTITÉ | Classement SNCC | Conserver. |
| 51 | `echeances` | 12 | ENTITÉ | Échéance | Conserver dans le détaillé. |
| 52 | `alertes` | 15 | ENTITÉ | Alerte | Conserver. |
| 53 | `notifications` | 15 | ENTITÉ | Notification | Conserver dans le détaillé. |
| 54 | `dossiers_veille` | 11 | ENTITÉ | Dossier de veille | Conserver. |
| 55 | `relances_veille` | 13 | ENTITÉ | Relance de veille | Conserver. |
| 56 | `rapports_veille` | 15 | ENTITÉ | Rapport de veille | Conserver. |
| 57 | `regles_metier` | 14 | ENTITÉ | Règle métier | Conserver dans le détaillé. |
| 58 | `revues_qualite` | 12 | ENTITÉ | Revue qualité | Conserver. |
| 59 | `plans_action` | 14 | ENTITÉ | Plan d’action | Conserver. |
| 60 | `decisions_institutionnelles` | 18 | ENTITÉ | Décision institutionnelle | Conserver. |
| 61 | `publications` | 17 | ENTITÉ | Publication | Conserver dans le détaillé. |
| 62 | `rapports_generes` | 17 | FUSION | Rapport généré | Présenter comme document produit, fusion conceptuelle avec Document. |
| 63 | `evenements_audit` | 15 | TECHNIQUE | — | Masquer du MCD ; documenter dans les règles d’audit. |
| 64 | `archives` | 13 | TECHNIQUE | — | Masquer du contracté ; conserver dans le MPD et l’architecture technique. |
| 65 | `sauvegardes` | 17 | TECHNIQUE | — | Masquer du MCD métier ; conserver dans le MPD. |
| 66 | `incidents` | 18 | ENTITÉ | Incident | Conserver dans le MCD détaillé. |

## Synthèse

- Entités conceptuelles conservées : **50**
- Tables transformées en associations : **7**
- Historiques conservés seulement dans le MCD détaillé : **2**
- Objets fusionnés ou absorbés : **3**
- Objets purement techniques masqués : **4**

## Règles de nettoyage du CDM

1. retirer `created_at`, `updated_at`, UUID, index, triggers et noms de contraintes ;
2. ne pas afficher les clés étrangères lorsqu’une association les représente ;
3. conserver les identifiants métier et les attributs compréhensibles par la HAUQE/GFA ;
4. remplacer les noms techniques par des noms métier au singulier ;
5. nommer chaque association avec un verbe ;
6. vérifier toutes les cardinalités minimales et maximales ;
7. produire un diagramme contracté et des diagrammes détaillés par domaine.
