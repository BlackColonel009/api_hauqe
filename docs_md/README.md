# HAUQE Certif

## Installation locale

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Lancement

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Si le port 8000 est déjà occupé :

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8013
```

Ouvrir ensuite `http://127.0.0.1:8000/` ou le port choisi.

## Architecture actuelle

```text
app/
├── main.py
├── templates/
│   ├── index.html              # structure unique de l'application
│   └── legacy/                 # vues de transition à convertir en modules
└── static/
    ├── css/
    └── js/
        ├── core/
        │   ├── api.js          # appels HTTP centralisés
        │   ├── app-shell.js    # sidebar et navbar communes
        │   ├── config.js       # configuration frontend
        │   └── router.js       # navigation dynamique
        └── fichiers des pages
```

La navigation utilise les routes `#/dashboard`, `#/alertes`, `#/echeances` et `#/entreprises`. La sidebar et la navbar ne sont créées qu'une seule fois.
