# Intégration des règles métier avec les domaines déjà développés

## Contrainte physique importante

Le MPD actuel impose :

```text
regles_metier.code UNIQUE
```

alors que les règles doivent être versionnées.

Aucune migration n'est faite.

Le lot utilise donc :

```text
code physique unique
+
version
+
parametres["_logical_code"]
```

Exemple :

```text
logical_code = VEILLE_SEUILS_EXPIRATION
version      = 1.0
code DB      = VEILLE_SEUILS_EXPIRATION__V1_0
```

Le fichier :

```text
app/rules/business_rule_resolver.py
```

est l'autorité commune pour récupérer une règle active.

## Veille

Dans `app/services/veille_service.py`, remplacer le lookup direct :

```python
rule = await WatchRepository.active_alert_rule(
    db,
    RULE_CODE_EXPIRATION,
)
```

par :

```python
from app.rules.business_rule_resolver import resolve_business_rule

rule = await resolve_business_rule(
    db,
    RULE_CODE_EXPIRATION,
)
```

La méthode `WatchRepository.active_alert_rule()` devient alors inutile et
peut être supprimée après validation.

## Collecte — complétude

Le même principe doit être appliqué au lookup :

```text
COLLECTE_COMPLETUDE
```

Au lieu de filtrer exclusivement :

```python
RegleMetier.code == "COLLECTE_COMPLETUDE"
```

utiliser :

```python
rule = await resolve_business_rule(
    db,
    "COLLECTE_COMPLETUDE",
)
```

## Pourquoi

Cela permet :
- historique des versions ;
- publication différée ;
- retrait ;
- absence de conflit avec la contrainte UNIQUE du MPD ;
- aucun changement de schéma.
