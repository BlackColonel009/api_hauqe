# Dépendances et configuration — Mon compte

## Dépendance Python

Ajouter à `requirements.txt` :

```text
cryptography>=42,<47
```

Aucune dépendance TOTP externe n'est requise : le TOTP RFC 6238 est implémenté
avec la bibliothèque standard.

## Settings

Ajouter dans `app/config/settings.py` les paramètres correspondants au style
déjà utilisé par le projet :

```python
MFA_FERNET_KEY: str | None = None
PASSWORD_RESET_URL_TEMPLATE: str | None = None
```

Exemple `.env` :

```env
MFA_FERNET_KEY=<CLE_FERNET>
PASSWORD_RESET_URL_TEMPLATE=https://votre-domaine.tg/#/mot-de-passe-oublie?token={token}
```

## Générer une clé Fernet

Exécuter une fois localement :

```powershell
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

La clé :
- reste dans `.env` / coffre de secrets ;
- n'est jamais envoyée au frontend ;
- n'est jamais enregistrée en base ;
- doit rester stable, sinon les secrets MFA existants deviennent
  indéchiffrables.

## Reset de mot de passe

Le frontend annonce déjà une expiration de 30 minutes. Le backend applique
donc exactement 30 minutes et un usage unique.

Si `PASSWORD_RESET_URL_TEMPLATE` n'est pas configuré, `/forgot` conserve sa
réponse neutre mais aucun email ne peut être mis en file. Ce cas est visible
dans l'audit serveur, pas dans la réponse publique.
