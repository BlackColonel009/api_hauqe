# Mapping frontend ↔ API — Pilotage / Tableaux de bord

## `index.html` — tableau opérationnel

Endpoint principal :

```text
GET /api/v1/dashboards/operational
```

Paramètres :

```text
days=7
zone_id=
sector=
norm_id=
organisme_id=
```

Filtres partagés :

```text
GET /api/v1/dashboards/filters
```

Définitions/infobulles :

```text
GET /api/v1/dashboards/indicator-definitions
```

Le endpoint opérationnel alimente :
- entreprises enregistrées ;
- certifications ;
- certifications actives ;
- nouvelles certifications de la période ;
- vigilance stratégique à 90 jours ;
- contrôles FUCCS à planifier ;
- alertes actives/critiques ;
- échéances en retard ;
- statuts des certifications ;
- buckets 180/90/30/expiration ;
- INFC national moyen ;
- actions prioritaires ;
- certifications récemment modifiées ;
- série d'activité.

Les filtres région/secteur/norme/organisme s'appliquent aux indicateurs de
registre/certification. Les alertes et échéances restent la file opérationnelle
globale tant que les ressources polymorphes ne portent pas toutes une
géographie normalisée.

---

## `/tableaux-de-bord/tactique`

```text
GET /api/v1/dashboards/tactical?year=2026&month=7
```

Alimente le pilotage mensuel Direction Technique :
- collecte ;
- vérification ;
- FUCCS ;
- décisions de validation ;
- intégrations ;
- alertes ;
- renouvellements ;
- revues qualité ;
- plans d'action ;
- comparaison avec le mois précédent.

---

## `/tableaux-de-bord/strategique`

```text
GET /api/v1/dashboards/strategic?year=2026&quarter=3
```

Alimente :
- chiffres nationaux ;
- répartition des statuts ;
- SNCC classe/risque ;
- régions ;
- secteurs ;
- normes ;
- organismes certificateurs ;
- tendance INFC sur quatre trimestres ;
- constats ;
- risques majeurs ;
- recommandations prioritaires.

La synthèse est déterministe et uniquement fondée sur les indicateurs
calculés. Elle ne remplace pas une décision institutionnelle.

---

## `/tableaux-de-bord/annuel`

```text
GET /api/v1/dashboards/annual?year=2026
```

Alimente :
- activité annuelle ;
- comparaison N/N-1 ;
- séries trimestrielles ;
- INFC ;
- SNCC ;
- géographie ;
- qualité ;
- incidents ;
- continuité/sauvegardes.

---

## `/barometre`

```text
GET /api/v1/barometer
GET /api/v1/barometer?start_date=2026-01-01&end_date=2026-06-30
```

Le baromètre affiche séparément :
- volume du registre ;
- certifications actives ;
- INFC moyen validé ;
- statuts ;
- SNCC ;
- régions ;
- secteurs ;
- normes ;
- organismes certificateurs.

Aucun indice composite supplémentaire n'est inventé.

---

## `/public`

```text
GET /api/v1/public/indicators
```

Le frontend public ne doit appeler **que** cet endpoint.

Il ne doit jamais appeler directement :
- `/entreprises`
- `/certifications`
- `/infc`
- `/sncc`
- `/audit`
- `/alertes`
- `/documents`

Le backend applique l'allowlist issue de la règle publiée et vérifie la
publication institutionnelle avant de retourner les agrégats.
