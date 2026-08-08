# Intégration des modèles et Alembic

## Pourquoi une extension du schéma est nécessaire

Le MPD initial de 66 tables ne contient pas les données nécessaires à des
fonctions déjà présentes dans `profil.html` :
- langue / fuseau / avatar ;
- préférences personnelles de notification ;
- secret MFA réel ;
- code privé hashé ;
- état de verrouillage par session ;
- jetons temporaires de reset/MFA.

L'extension a donc été explicitement créée.

## Nouvelles tables

```text
preferences_utilisateur
securite_compte_utilisateur
verrous_session_utilisateur
jetons_securite_utilisateur
```

Le schéma métier passe de **66 à 70 tables**.

## Migration

Fichier :

```text
alembic/versions/c5b7a8f2d901_account_security_extension.py
```

Chaîne :

```text
9f89b5d85b6a
      ↓
c5b7a8f2d901
```

Commande :

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Puis :

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

Attendu :

```text
c5b7a8f2d901 (head)
```

## Registre des modèles

Si `app/models/__init__.py` importe explicitement chaque modèle, ajouter :

```python
from app.models.preference_utilisateur import PreferenceUtilisateur
from app.models.securite_compte_utilisateur import SecuriteCompteUtilisateur
from app.models.verrou_session_utilisateur import VerrouSessionUtilisateur
from app.models.jeton_securite_utilisateur import JetonSecuriteUtilisateur
```

Si `alembic/env.py` importe explicitement les modèles pour construire
`Base.metadata`, ajouter également ces quatre imports avant toute future
autogénération.

## MCD / MLD / MPD

Les fichiers historiques PowerDesigner restent la référence de la version
initiale 66 tables.

Cette extension doit être reportée dans le prochain cycle documentaire
MCD/MLD/MPD afin que la documentation physique rejoigne le schéma runtime.
