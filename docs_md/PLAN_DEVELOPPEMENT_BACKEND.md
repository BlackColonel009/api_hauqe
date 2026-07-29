# Plan de développement — Base PostgreSQL et API FastAPI

> Projet : HAUQE Certif  
> Version : 1.1  
> Date : 23 juillet 2026  
> Statut : plan initial à exécuter  
> Référence normative : règles métier RM-01 à RM-51 validées par la HAUQE/GFA

## 1. Objectif

Construire une base nationale des entreprises certifiées et une API FastAPI sécurisée, versionnée, testée et raccordable au frontend existant.

Le backend doit appliquer le cycle métier complet :

**Brouillon → Soumise → Vérification → Contrôle FUCCS → Validation définitive → Intégration BNEC → Classification entreprise / INFC → SNCC → Veille**

Les calculs, validations, permissions, transitions de statut et événements d'audit doivent être exécutés côté FastAPI/PostgreSQL. Le JavaScript ne doit servir qu'à l'interface.

## 2. Corpus de référence

Ordre d'interprétation :

1. règles métier RM-01 à RM-51 validées ;
2. procédures et formulaires opérationnels ;
3. documents spécialisés INFC et SNCC ;
4. guide méthodologique ;
5. propositions et simulations du frontend.

Documents de continuité :

- `PASSATION_PROJET_HAUQE_CERTIF.md` ;
- `FEUILLE_DE_ROUTE_FRONTEND.md` ;
- `GUIDE_UTILISATION.md` ;
- `SUIVI_LIVRABLES_HAUQE_CERTIF.md`.

Trois futures règles métier sont annoncées mais non reçues. Elles ne seront ni inventées ni codées avant leur communication.

## 3. Principes d'architecture

### 3.1 Technologies

- Python et FastAPI ;
- PostgreSQL ;
- SQLAlchemy 2 en mode asynchrone ;
- Psycopg 3 comme pilote PostgreSQL ;
- Alembic pour les migrations ;
- Pydantic 2 et Pydantic Settings ;
- Argon2id pour les mots de passe et codes de reprise de session ;
- Pytest pour les tests ;
- tâches en arrière-plan pour notifications et petits travaux différés ;
- mécanisme de file de tâches à introduire avant les traitements lourds de rapports et d'import.

### 3.2 Organisation cible

```text
backend/
├── app/
│   ├── config/
│   │   ├── settings.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── types.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   │   ├── dependencies.py
│   │   ├── web.py
│   │   └── api/
│   │       └── v1/
│   │           ├── router.py
│   │           ├── auth.py
│   │           ├── enterprises.py
│   │           ├── certification_bodies.py
│   │           ├── certifications.py
│   │           ├── collections.py
│   │           ├── verifications.py
│   │           ├── controls.py
│   │           ├── validations.py
│   │           ├── integrations.py
│   │           └── ...
│   ├── repositories/
│   │   ├── base.py
│   │   └── ...
│   ├── services/
│   ├── rules/
│   │   ├── certifications.py
│   │   ├── enterprises.py
│   │   ├── duplicates.py
│   │   ├── completeness.py
│   │   ├── transitions.py
│   │   ├── alerts.py
│   │   ├── fuccs.py
│   │   ├── infc.py
│   │   └── sncc.py
│   ├── permissions/
│   ├── middleware/
│   ├── audit/
│   ├── tasks/
│   ├── utils/
│   ├── uploads/
│   │   ├── avatars/
│   │   ├── produits/
│   │   ├── documents/
│   │   ├── rapports/
│   │   └── temporaires/
│   ├── static/
│   ├── templates/
│   └── main.py
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── api/
│   └── conftest.py
├── requirements.txt
├── .env
├── .env.example
├── alembic.ini
└── README.md
```

Cette structure devient la convention officielle du backend HAUQE Certif.

### 3.3 Responsabilités des couches

| Couche | Responsabilité |
|---|---|
| `routes/web.py` | Servir le shell frontend, les fragments HTML et les vues |
| `routes/api/v1/` | Exposer les endpoints JSON versionnés |
| `schemas/` | Valider les entrées et structurer les réponses Pydantic |
| `services/` | Orchestrer les parcours métier et les transactions |
| `repositories/` | Interroger et modifier PostgreSQL avec SQLAlchemy |
| `rules/` | Exécuter les règles RM, transitions et calculs métier |
| `permissions/` | Appliquer les habilitations et contrôles de périmètre |
| `audit/` | Produire et consulter les événements de traçabilité |
| `tasks/` | Exécuter les notifications, rapports et traitements différés |
| `middleware/` | Gérer les préoccupations HTTP transversales |
| `utils/` | Fournir uniquement des utilitaires génériques sans logique métier |

Le flux standard sera :

```text
Route API → Service métier → Repository → SQLAlchemy → PostgreSQL
                    ↓
             Règles / Audit / Tâches
```

Les repositories réalisent les accès aux données et utilisent `flush()` lorsque nécessaire, mais ne valident pas seuls les transactions métier. Le service ou l'unité de travail contrôle le `commit` ou le `rollback` de l'opération complète.

### 3.4 Application FastAPI unique

`backend/app/main.py` reste le point d'entrée unique. Il configure FastAPI puis monte séparément :

- les routes frontend sous `/` et `/views/...` ;
- les ressources frontend sous `/static/...` ;
- l'API métier sous `/api/v1/...` ;
- la route de santé générale et technique.

Le fichier `main.py` ne doit contenir aucune règle métier ni requête SQL.

### 3.5 Stockage et configuration

- `backend/.env` contient les secrets locaux et ne doit jamais être versionné ;
- `backend/.env.example` documente uniquement les variables attendues ;
- les documents métier restent dans un stockage privé ;
- le dossier `uploads/` ne doit pas être monté comme un répertoire statique public ;
- les téléchargements passent par une route API contrôlant permission, périmètre et audit ;
- les avatars peuvent recevoir une politique dédiée, distincte des preuves métier ;
- le stockage pourra ultérieurement être remplacé par un service objet sans modifier les services métier.

### 3.6 Conventions de données

- clés techniques en UUID ;
- identifiants nationaux métier permanents et non réattribuables ;
- dates techniques en `timestamptz` UTC, affichées en `Africa/Lome` ;
- dates civiles en `date` ;
- scores et pondérations en `numeric`, jamais en flottant ;
- suppression logique et archivage motivé ;
- contrôle de concurrence par colonne de version ;
- historisation des données sensibles et des transitions ;
- contraintes et index définis dans les migrations ;
- paramètres métier versionnés, publiés et audités ;
- stockage documentaire hors du répertoire public.

## 4. Stratégie de réalisation

Le développement sera incrémental. Chaque lot doit produire :

- une migration Alembic ;
- des modèles SQLAlchemy ;
- des schémas Pydantic ;
- des services métier ;
- des routes API ;
- les permissions nécessaires ;
- des événements d'audit ;
- des tests ;
- une mise à jour documentaire ;
- un raccordement frontend lorsqu'il est utile au lot.

Une fonctionnalité n'est terminée que si son parcours nominal, ses erreurs, ses permissions et son audit sont testés.

## 5. Phases de développement

### Phase 0 — Conception de référence

**Objectif :** figer un socle cohérent avant toute migration métier.

Travaux :

1. construire le modèle conceptuel de données ;
2. établir les entités, associations et cardinalités ;
3. produire les règles de gestion conceptuelles ;
4. construire le dictionnaire de données ;
5. publier le catalogue unique des statuts et transitions ;
6. établir la matrice rôles/permissions ;
7. établir la matrice RM → écran → permission → table → API → audit → test ;
8. dériver le modèle logique de données ;
9. définir les agrégats transactionnels et frontières de services ;
10. relever les derniers arbitrages sans bloquer les éléments déjà validés.

Livrables :

- `MCD_HAUQE_CERTIF.md` ;
- diagramme MCD ;
- dictionnaire de données ;
- catalogue des statuts ;
- matrice des permissions ;
- matrice de traçabilité RM.

Critères de sortie :

- aucune relation plusieurs-à-plusieurs non résolue ;
- FUCCS, classification entreprise, INFC et SNCC modélisés séparément ;
- versions déclarées, officielles et historiques distinguées ;
- étapes vérification, contrôle, validation et intégration distinctes ;
- cardinalités et règles critiques relues.

### Phase 1 — Socle technique FastAPI/PostgreSQL

**Objectif :** obtenir une application connectée à PostgreSQL avec migrations et tests.

Travaux :

1. compléter les dépendances Python ;
2. ajouter une configuration par variables d'environnement ;
3. configurer la connexion asynchrone PostgreSQL ;
4. initialiser SQLAlchemy et Alembic ;
5. créer les classes communes d'identifiant, audit, version et archivage ;
6. configurer les exceptions et réponses API ;
7. créer les environnements développement et test ;
8. ajouter les tests de santé API et base ;
9. conserver les routes frontend existantes.

Critères de sortie :

- connexion à PostgreSQL vérifiée ;
- migration initiale applicable et réversible ;
- endpoint `/api/health` vérifiant application et base ;
- tests exécutables localement ;
- aucun secret enregistré dans Git.

### Phase 2 — Sécurité, utilisateurs et habilitations

**Objectif :** sécuriser tous les lots suivants.

Périmètre :

- utilisateurs, rôles, permissions et périmètres ;
- invitations et activation ;
- authentification et renouvellement de session ;
- déconnexion et révocation ;
- mot de passe oublié ;
- sessions actives ;
- verrouillage de compte après cinq échecs ;
- inactivité de compte à 180 jours et préavis à 30 jours ;
- code privé de reprise de session, distinct du verrouillage du compte ;
- événements de sécurité ;
- préférences de notification.

Routes principales :

```text
/api/v1/auth/*
/api/v1/users
/api/v1/roles
/api/v1/permissions
/api/v1/me
/api/v1/security-events
```

Critères de sortie :

- mots de passe et codes privés hachés ;
- cookies ou jetons configurés de façon sécurisée ;
- permissions contrôlées côté serveur ;
- opérations sensibles auditées ;
- tests de refus d'accès et de révocation réussis.

### Phase 3 — Référentiels, règles et codification

**Objectif :** fournir les valeurs partagées et la configuration versionnée.

Périmètre :

- régions, préfectures, communes et localités ;
- secteurs, activités, produits, unités et marchés ;
- normes et référentiels ;
- types de documents, décisions, motifs et niveaux de risque ;
- versions des règles métier ;
- paramètres et règles de complétude ;
- modèles de scoring et pondérations ;
- modèles de codes et séquences transactionnelles ;
- circuit Brouillon → Soumis → Approuvé → Publié → Retiré.

Critères de sortie :

- référentiels initialisés sans valeurs métier codées dans le frontend ;
- version publiée immuable ;
- codes générés sans collision sous concurrence ;
- changement de paramètre entièrement audité.

### Phase 4 — Entreprises et qualité d'identité

**Objectif :** rendre opérationnel le registre national des entreprises.

Périmètre :

- entreprise et versions administratives ;
- contacts, sites, produits, marchés et activités ;
- géolocalisation ;
- RCCM et NIF/IFU ;
- enregistrement sans RCCM avec statut de régularisation ;
- identifiant national permanent ;
- détection multicritère des doublons ;
- score de complétude ;
- archivage sans suppression ;
- historique et documents.

Règles critiques :

- RCCM unique lorsqu'il est renseigné ;
- minimum : nom, localité, région et téléphone ou courriel ;
- doublons examinés avant validation ;
- aucune réutilisation de code national.

### Phase 5 — Organismes, accréditations et certifications

**Objectif :** constituer le cœur du registre des certifications.

Périmètre :

- organismes et versions ;
- accréditations structurées par référentiel, domaine, périmètre et validité ;
- historique des statuts d'accréditation ;
- certifications et versions ;
- produits et sites couverts ;
- audits de certification ;
- pièces officielles ;
- authenticité et état de vérification ;
- procédures et preuves de renouvellement ;
- historique des statuts.

Règles critiques :

- unicité entreprise–organisme–référentiel–périmètre ;
- date d'obtention obligatoire ;
- expiration facultative seulement si le référentiel l'autorise ;
- cohérence chronologique bloquante ;
- justificatif officiel obligatoire, sinon « À vérifier » ;
- organisme non accrédité autorisé, certificats associés à vérifier ;
- statut « Non renouvelée » six mois après expiration hors procédure justifiée.

### Phase 6 — Documents et stockage de preuves

**Objectif :** sécuriser les fichiers utilisés par tous les parcours.

Périmètre :

- téléversement contrôlé ;
- métadonnées, type, source et auteur ;
- MIME et taille autorisés ;
- checksum ;
- version et statut ;
- analyse antivirus si disponible ;
- liens explicites vers les ressources métier ;
- accès et téléchargement selon permission ;
- archivage et conservation.

Critères de sortie :

- aucun fichier métier servi directement depuis un chemin public ;
- contrôle d'accès appliqué au téléchargement ;
- intégrité vérifiable ;
- anciennes versions conservées.

### Phase 7 — Campagnes, missions et collecte

**Objectif :** remplacer les brouillons `localStorage` par des dossiers serveur versionnés.

Périmètre :

- campagnes et objectifs ;
- missions et affectations d'agents ;
- formulaires et révisions ;
- produits, marchés et certifications déclarés ;
- consentement et signature ;
- calcul de complétude ;
- brouillon incomplet autorisé ;
- soumission bloquée si incomplète ;
- suivi des fiches papier à saisir sous cinq jours ouvrables ;
- corrections et nouvelles versions.

Critères de sortie :

- une seule révision courante par mission ;
- valeurs déclarées conservées après intégration ;
- soumission transactionnelle ;
- historique des statuts complet.

### Phase 8 — Vérification documentaire et échanges

**Objectif :** créer l'étape P0 absente du frontend initial.

Périmètre :

- affectation à un vérificateur ;
- contrôles de complétude, dates, portée, norme et accréditation ;
- sources et preuves de vérification ;
- anomalies et escalades ;
- demandes officielles aux organismes ou entreprises ;
- réponses, pièces, délais et relances ;
- avis normalisés.

Avis :

```text
verified_compliant
verified_with_reservation
not_verified
suspect
rejected
```

Critères de sortie :

- aucune vérification confondue avec la validation ;
- toutes les demandes et réponses traçables ;
- retours et réserves motivés ;
- cas suspects escaladés selon permission.

### Phase 9 — Contrôle FUCCS

**Objectif :** implémenter la grille officielle sans la confondre avec l'INFC.

Périmètre :

- versions de grille ;
- quatre rubriques officielles ;
- 28 critères ;
- notes 0, 1 ou 2 ;
- score maximal 56 et taux de conformité ;
- commentaires, preuves et constats ;
- risques et actions correctives ;
- finalisation et éventuelle réouverture autorisée.

Critères de sortie :

- ancienne grille reproductible après changement ;
- score recalculable depuis les notes ;
- commentaires obligatoires selon la règle active ;
- contrôle finalisé non modifiable sans procédure tracée.

### Phase 10 — Validation hiérarchique et intégration BNEC

**Objectif :** séparer la décision formelle de l'intégration technique.

Périmètre validation :

- affectations ;
- visas de premier et second niveau ;
- décisions validé, validé sous réserve, ajourné ou rejeté ;
- réserves, motifs et preuves ;
- demandes de correction ;
- double validation.

Périmètre intégration :

- file des dossiers formellement validés ;
- précontrôle des doublons et identifiants ;
- attribution des codes ;
- création ou mise à jour des données officielles ;
- contrôle post-intégration ;
- erreurs, reprise et notification ;
- sauvegarde de référence.

Critères de sortie :

- intégration techniquement impossible sans validation formelle ;
- données déclarées et données officielles séparées ;
- chaque élément intégré relié à sa révision source ;
- contrôles avant/après et erreurs historisés.

### Phase 11 — Classification entreprise, INFC et SNCC

**Objectif :** produire trois résultats indépendants et reproductibles.

#### Classification entreprise

- Conforme : 85–100 ;
- À surveiller : 60–84 ;
- Non conforme : moins de 60.

#### INFC

- score propre à une certification sur 100 ;
- six domaines pondérés ;
- formule, données sources, arrondis et traitement des manquants versionnés ;
- niveaux et agrégats séparés.

#### SNCC

- classes A+ à D ;
- statuts VA, RE, SU, RT, EX et VE ;
- risques R1 à R5 ;
- proposition, vérification et validation ;
- historique des reclassements.

Critères de sortie :

- aucune règle de trois silencieuse FUCCS → INFC ;
- modèle et version visibles pour chaque résultat ;
- données insuffisantes signalées sans score trompeur ;
- historique complet.

### Phase 12 — Échéances, alertes, notifications et veille

**Objectif :** automatiser le suivi des certifications.

Niveaux validés :

| Niveau | Déclenchement |
|---|---:|
| Information | 180 jours avant expiration |
| Surveillance | 90 jours avant expiration |
| Urgence | 30 jours avant expiration |
| Critique | À l'expiration |

Périmètre :

- génération et déduplication ;
- alertes spéciales ;
- affectation et résolution ;
- relances et escalades ;
- courriels en arrière-plan ;
- historique des envois et erreurs ;
- dossiers de veille ;
- analyse hebdomadaire ;
- notes mensuelles ;
- rapports trimestriels ;
- indicateurs CVC.

Critères de sortie :

- alerte critique maintenue jusqu'à régularisation ou clôture ;
- comptes inactifs ou bloqués exclus des destinataires ;
- envois retentés et audités ;
- aucun doublon d'alerte active pour la même règle et échéance.

### Phase 13 — Décisions, qualité, archivage et continuité

**Objectif :** couvrir la gouvernance durable de la BNEC.

Périmètre :

- notes de décision et décisions institutionnelles ;
- plans d'action et revues d'effet ;
- campagnes annuelles de qualité ;
- constats et actions correctives ;
- archives et politiques de conservation ;
- conservation minimale de dix ans ;
- politiques et exécutions de sauvegarde ;
- demandes et tests de restauration ;
- incidents et événements techniques.

### Phase 14 — Rapports, publications et tableaux de bord

**Objectif :** alimenter les outils de pilotage avec des données fiables.

Périmètre :

- tableaux opérationnel, tactique, stratégique, annuel et public ;
- agrégats par période, région, secteur, norme et organisme ;
- modèles de rapports ;
- tâches de génération PDF, XLSX et CSV ;
- historique et téléchargement sécurisé ;
- exports sensibles avec permission et motif ;
- publications Brouillon → Soumis → Approuvé → Publié → Retiré ;
- indicateurs publics agrégés et isolés des données confidentielles.

### Phase 15 — Raccordement frontend et recette finale

**Objectif :** remplacer toutes les simulations par les API.

Ordre de raccordement :

1. authentification et profil ;
2. référentiels ;
3. entreprises ;
4. organismes et accréditations ;
5. certifications ;
6. documents ;
7. collecte ;
8. vérification ;
9. contrôle FUCCS ;
10. validation et intégration ;
11. classification, INFC et SNCC ;
12. alertes, échéances et veille ;
13. rapports, tableaux de bord et administration.

Recette :

- tests API ;
- tests des permissions ;
- tests des transitions ;
- tests de calcul ;
- tests de concurrence et doublons ;
- tests d'import et d'export ;
- tests des documents ;
- tests de sécurité ;
- test complet du parcours métier ;
- recette écran par écran.

## 6. Ordre de livraison recommandé

### Lot A — Fondations

Phases 0 à 3 : conception, socle, sécurité et référentiels.

### Lot B — Registre BNEC

Phases 4 à 6 : entreprises, organismes, certifications et documents.

### Lot C — Chaîne de traitement

Phases 7 à 10 : collecte, vérification, contrôle, validation et intégration.

### Lot D — Évaluation et veille

Phases 11 à 13 : classification, INFC, SNCC, alertes, CVC, qualité et continuité.

### Lot E — Pilotage et mise en service

Phases 14 et 15 : rapports, tableaux de bord, raccordement, recette et transfert.

## 7. Sujets ouverts à traiter comme paramètres

- format national définitif des codes et remise à zéro des séquences ;
- formule opérationnelle complète de l'INFC ;
- détails de la matrice SNCC et règles de reclassement ;
- habilitations exactes des deux niveaux de validation ;
- visa ou signature électronique ;
- information complémentaire éventuelle à 12 mois ;
- fréquence définitive des relances ;
- périmètre des données publiques ;
- charte et modèles officiels des rapports ;
- hébergement et mécanisme d'envoi des courriels.

Ces sujets ne doivent pas empêcher la modélisation, mais aucune valeur provisoire ne doit être publiée comme règle définitive.

## 8. Contrôle d'avancement

Pour chaque phase, suivre :

| Élément | Attendu |
|---|---|
| Conception | modèle et règles documentés |
| Base | migration versionnée et testée |
| API | routes documentées dans OpenAPI |
| Sécurité | permissions et cas de refus testés |
| Audit | événements attendus vérifiés |
| Tests | succès nominal, erreurs et limites |
| Frontend | données simulées remplacées |
| Documentation | guide, passation et livrables actualisés |
| Validation | décision et preuve enregistrées |

## 9. Première séquence d'exécution

1. produire `MCD_HAUQE_CERTIF.md` ;
2. produire le diagramme conceptuel par domaines ;
3. établir le dictionnaire conceptuel ;
4. établir les statuts et transitions ;
5. établir la matrice rôles/permissions ;
6. établir la matrice de traçabilité RM ;
7. dériver le MLD PostgreSQL ;
8. valider les noms, relations et contraintes ;
9. initialiser le socle FastAPI/SQLAlchemy/Alembic ;
10. connecter l'instance PostgreSQL locale.

Le premier développement de code commencera après stabilisation suffisante du MCD et du MLD.
