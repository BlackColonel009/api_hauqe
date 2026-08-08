# Interactions — Échéances / Alertes / Notifications / Veille

```text
CERTIFICATIONS
├── date_expiration
├── AUDITS_CERTIFICATION.date_prevue
└── RENOUVELLEMENTS_CERTIFICATION.date_limite
              ↓
        SCAN QUOTIDIEN
              ↓
          ECHEANCES
              ↓
           ALERTES
              ├────────→ NOTIFICATIONS
              │           ├── IN_APP
              │           └── EMAIL / autres transports
              │
              └────────→ traitement / affectation / résolution
                              ↓
                       DOSSIERS_VEILLE
                              ↓
                       RELANCES_VEILLE
                              ↓
                       RAPPORTS_VEILLE
```

## Ressources polymorphes

Le MPD utilise :

```text
echeances.ressource_type + ressource_id
alertes.ressource_type + ressource_id
```

Le moteur conserve donc ces liens sans ajouter de FK.

Les FK explicites existantes sont préservées :
- `alertes.echeance_id`
- `notifications.alerte_id`
- `dossiers_veille.certification_id`
- `relances_veille.dossier_veille_id`

## Historique

Aucune suppression physique n'est exposée.

La résolution d'une alerte conserve :
- ligne d'alerte ;
- date de résolution ;
- notifications ;
- audit du motif.

Les relances conservent :
- destinataire ;
- canal ;
- envoi ;
- échéance ;
- réponse ;
- résultat.

## Rapports CVC

Les indicateurs du rapport sont calculés sur une période ISO :

```text
YYYY-MM-DD → YYYY-MM-DD
```

Même si le MPD stocke `periode_debut` et `periode_fin` en VARCHAR, le service
valide le format puis stocke la forme ISO afin de garder une comparaison
cohérente.
