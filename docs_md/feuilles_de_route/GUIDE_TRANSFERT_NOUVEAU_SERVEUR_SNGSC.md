# Guide de transfert du SNGSC vers un nouveau serveur Linux

**Version du 01/10/2026 — scénario : conservation intégrale des données et des comptes.**

Ce guide complète la [feuille de route d'hébergement](FEUILLE_DE_ROUTE_HEBERGEMENT_SNGSC.md). Il décrit une **restauration complète**, pas une installation vierge. Les commandes d'exemple supposent Debian/Ubuntu, PostgreSQL local, le dépôt dans `/var/www/api_hauqe`, la base `hauqe_certif`, le rôle SQL `hauqe_app` et le service `sngsc`. Vérifier ces valeurs sur les deux serveurs avant de les utiliser. Aucun mot de passe réel ne doit figurer dans ce document, une commande ou Git.

## 1. Règles de la bascule

1. Préparer le nouveau serveur et vérifier les sauvegardes avant de couper l'ancien.
2. Pour la sauvegarde finale, **arrêter l'application de l'ancien serveur** et empêcher tout nouvel accès en écriture. Le worker SMTP et les sauvegardes démarrent avec FastAPI : ne pas laisser les deux instances actives en parallèle sur les mêmes données.
3. Transférer ensemble : une archive PostgreSQL complète, `uploads/`, `app/uploads/avatars/`, les archives `backups/` si leur historique doit rester téléchargeable, ainsi que les secrets indispensables de `.env` par un canal sécurisé.
4. Sur le nouveau serveur, restaurer **d'abord** la base et les fichiers ; vérifier la révision Alembic restaurée ; appliquer ensuite uniquement les migrations qui lui manquent. Ne pas lancer `bootstrap_security` ni des seeds de première installation sur la base restaurée : comptes, rôles, permissions et historiques sont déjà dedans.
5. Tester FastAPI sur `127.0.0.1:8014` avant Nginx, puis installer le service permanent, le proxy et HTTPS.
6. Ne pas faire `alembic stamp`, `DROP`, `TRUNCATE` ou réinitialisation de la base pour contourner une erreur. En cas d'échec, conserver l'ancien serveur arrêté ou revenir à son état connu après décision explicite.

**État du dépôt contrôlé le 01/10/2026 :** une seule tête Alembic, `k6a0c4e8f2b3` ; la migration est suivie par Git. Ce numéro est un repère daté, **pas** une constante : sur le nouveau serveur, `python -m alembic heads` fait foi après le `git pull` de la version à déployer.

Le script historique `scripts/preflight_hebergement_linux.sh` contient encore une ancienne tête Alembic codée en dur (`h3d9e4f1a607`) : ne pas prendre son résultat comme verdict de migration tant qu'il n'a pas été actualisé. Utiliser les contrôles `alembic current` / `alembic heads` de ce guide.

## 2. Préparation avant l'interruption

Sur l'ancien serveur, relever et conserver hors de Git :

```bash
cd /var/www/api_hauqe
git rev-parse HEAD
git branch --show-current
git status --short
source .venv/bin/activate
python -m alembic current
python -m alembic heads
sudo -u postgres psql -d hauqe_certif -Atc 'SELECT version_num FROM alembic_version;'
df -h /var/www/api_hauqe
```

Si Git contient des modifications locales utiles, les qualifier et les préserver avant tout `pull`. Vérifier que le commit voulu et toutes ses migrations ont été poussés vers le dépôt auquel le nouveau serveur accèdera. Évaluer la taille de la base, des documents et des archives, puis réserver assez d'espace pour le dépôt, le transfert, la restauration et une sauvegarde supplémentaire. Tester l'accès SSH, PostgreSQL, Python, `pg_dump`, `pg_restore`, Nginx et le DNS à l'avance.

Choisir dès maintenant la future adresse publique. Les liens de réinitialisation de mot de passe et les liens envoyés dans les courriels devront utiliser cette adresse. Prévoir une fenêtre de maintenance : l'ancien serveur reste la référence tant que la bascule n'est pas validée.

## 3. Installer le code et PostgreSQL sur le nouveau serveur

Installer les paquets système adaptés à la distribution : Git, Python 3 avec `venv`, PostgreSQL client et serveur, Nginx et les bibliothèques nécessaires aux dépendances Python. Vérifier que `pg_restore` du nouveau serveur sait lire le format de l'archive produite sur l'ancien ; privilégier une version PostgreSQL cible identique ou plus récente, après validation de compatibilité.

```bash
cd /var/www
git clone URL_DU_DEPOT api_hauqe
cd /var/www/api_hauqe
git rev-parse HEAD
git status --short
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m alembic heads
```

Comparer le commit et la tête Alembic avec ceux prévus. **Ne pas lancer `alembic upgrade head` à ce stade** : la sauvegarde contient déjà le schéma et la table `alembic_version`.

Créer le rôle SQL et une base **vide** ; ne pas y créer les tables applicatives. Dans `sudo -u postgres psql` :

```sql
CREATE ROLE hauqe_app LOGIN;
\password hauqe_app
CREATE DATABASE hauqe_certif OWNER hauqe_app TEMPLATE template0;
\quit
```

La commande `\password` demande le secret sans l'inscrire en clair dans l'historique shell. Si le rôle ou la base existe déjà, vérifier leur état ; ne pas répéter `CREATE` aveuglément. Le mot de passe du **rôle SQL** peut changer sur le nouveau serveur : cela ne change pas les identifiants des utilisateurs HAUQE conservés dans la base.

## 4. Arrêt de l'ancien serveur et sauvegarde finale

Une fois le nouveau serveur prêt à recevoir les archives, bloquer les accès publics à l'ancienne application et arrêter son service. Confirmer l'arrêt avant la sauvegarde finale :

```bash
sudo systemctl stop sngsc
systemctl is-active sngsc
```

`inactive` est attendu. Dans une session disposant des droits de sauvegarde, créer un répertoire privé et produire les archives. Les chemins `uploads`, `app/uploads/avatars` et `backups` doivent être vérifiés avant de lancer `tar` ; ne pas les remplacer par un chemin approximatif.

```bash
cd /var/www/api_hauqe
umask 077
mkdir -p "$HOME/sngsc-transfer"
sudo -u postgres pg_dump -Fc --no-owner --no-acl hauqe_certif \
  > "$HOME/sngsc-transfer/hauqe_certif.dump"
tar -czf "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" \
  uploads app/uploads/avatars backups
pg_restore --list "$HOME/sngsc-transfer/hauqe_certif.dump" > /dev/null
tar -tzf "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" > /dev/null
sha256sum "$HOME/sngsc-transfer/hauqe_certif.dump" \
  "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" \
  > "$HOME/sngsc-transfer/SHA256SUMS"
```

L'archive `backups/` préserve les fichiers auxquels peuvent faire référence les anciennes politiques et exécutions de sauvegarde. Si elle n'existe pas, noter explicitement ce qui manque et créer une archive seulement avec les répertoires présents. Ne pas assimiler le statut `TERMINE` d'une sauvegarde dans l'interface à une restauration testée.

Copier les deux archives et `SHA256SUMS` vers un répertoire privé du nouveau serveur avec `scp` ou `rsync` sur SSH. Exemple à adapter depuis l'ancien serveur :

```bash
scp "$HOME/sngsc-transfer/hauqe_certif.dump" \
    "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" \
    "$HOME/sngsc-transfer/SHA256SUMS" \
    UTILISATEUR_NOUVEAU_SERVEUR@HOTE_NOUVEAU_SERVEUR:~/sngsc-transfer/
```

Le répertoire `~/sngsc-transfer` doit déjà exister sur le nouveau serveur (`umask 077; mkdir -p ~/sngsc-transfer`). Ne pas placer ces archives dans le dépôt Git ni dans un répertoire servi par Nginx. Transférer les valeurs secrètes de l'ancien `.env` par un canal sécurisé séparé ; ne jamais les coller dans un ticket ou une sortie de diagnostic.

## 5. Restaurer sur le nouveau serveur

Contrôler d'abord les empreintes et la liste du contenu, puis copier l'archive SQL dans un répertoire lisible par le compte PostgreSQL :

```bash
cd "$HOME/sngsc-transfer"
sha256sum -c SHA256SUMS
pg_restore --list hauqe_certif.dump | head
tar -tzf sngsc-fichiers.tar.gz | head
sudo install -d -o postgres -g postgres -m 700 /var/lib/postgresql/sngsc-transfer
sudo install -o postgres -g postgres -m 600 hauqe_certif.dump \
  /var/lib/postgresql/sngsc-transfer/hauqe_certif.dump
```

Sur une base cible fraîche et vide, restaurer **une seule fois** :

```bash
sudo -u postgres pg_restore --no-owner --no-acl --role=hauqe_app \
  --exit-on-error --single-transaction -d hauqe_certif \
  /var/lib/postgresql/sngsc-transfer/hauqe_certif.dump
sudo -u postgres psql -d hauqe_certif \
  -c 'SELECT version_num FROM alembic_version;'
```

Ne pas relancer la restauration sur une base partiellement peuplée après une erreur ; diagnostiquer le message et décider d'un nouveau départ sûr avec sauvegarde et cible explicitement vérifiées. Vérifier aussi que le rôle applicatif peut lire et écrire ses tables : le `--role=hauqe_app` doit lui attribuer les objets restaurés.

Sur le clone neuf, inspecter le contenu de l'archive de fichiers puis extraire au bon emplacement. Cette extraction est prévue **uniquement** sur un nouveau dépôt dont les dossiers de données ne contiennent pas de fichiers à préserver :

```bash
cd /var/www/api_hauqe
tar -tzf "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" | head -50
tar -xzf "$HOME/sngsc-transfer/sngsc-fichiers.tar.gz" -C /var/www/api_hauqe
id sngsc || sudo useradd --system --home /var/www/api_hauqe \
  --shell /usr/sbin/nologin sngsc
sudo install -d -o sngsc -g sngsc -m 750 \
  logs backups uploads uploads/private app/uploads/avatars
sudo chown -R sngsc:sngsc backups uploads app/uploads/avatars
```

Ne jamais extraire une archive reçue d'une provenance inconnue. Les chemins internes doivent être relatifs à la racine du dépôt et ne contenir ni `..` ni chemin absolu. Conserver hors du dossier public les documents et les archives.

## 6. Configurer `.env` puis aligner Alembic

Créer `/var/www/api_hauqe/.env` sur le nouveau serveur via `sudoedit`. Reprendre les secrets nécessaires de l'ancien environnement sans publier leur valeur :

- `MFA_FERNET_KEY` : **exactement la même** si des utilisateurs ont déjà activé le MFA ; sinon leurs secrets TOTP ne seront plus déchiffrables ;
- `SECRET_KEY` : conserver la valeur pendant le transfert pour préserver la continuité de la configuration d'authentification ; planifier toute rotation séparément ;
- `DATABASE_URL=postgresql+psycopg://hauqe_app:...@localhost:5432/hauqe_certif` : utiliser le mot de passe du nouveau rôle SQL ; encoder les caractères spéciaux dans l'URL ;
- `ENVIRONMENT=production`, `DEBUG=false`, `TIMEZONE=Africa/Lome` et les paramètres de session ;
- `HAUQE_SMTP_*` et `HAUQE_CONTACT_*` : vérifier les identifiants SMTP et la signature ;
- `PASSWORD_RESET_URL_TEMPLATE` et `LIEN_VERS_SNGSC` : les remplacer par l'adresse **du nouveau site**, une fois celle-ci définie.

```bash
cd /var/www/api_hauqe
sudo chown root:sngsc .env
sudo chmod 640 .env
source .venv/bin/activate
python -m alembic heads
python -m alembic current
```

Comparer `current` (révision de la base restaurée) à `heads` (révision du code). Si elles sont différentes mais forment une chaîne Alembic connue, faire une sauvegarde de la base restaurée avant la migration, puis :

```bash
python -m alembic upgrade head
python -m alembic current
sudo -u postgres psql -d hauqe_certif \
  -c 'SELECT version_num FROM alembic_version;'
```

Si `current` est déjà égal à `heads`, aucune migration n'est à appliquer. Si la révision restaurée est inconnue du code ou s'il existe plusieurs têtes non prévues, **s'arrêter**. Ne pas lancer de bootstrap, seed ou script de rattrapage historique simplement parce que le serveur est nouveau.

## 7. Vérifier les données avant de démarrer l'application

Comparer les résultats de l'ancien serveur sauvegardé et du nouveau :

```bash
sudo -u postgres psql -d hauqe_certif -c \
  'SELECT count(*) AS utilisateurs FROM utilisateurs;'
sudo -u postgres psql -d hauqe_certif -c \
  'SELECT count(*) AS entreprises FROM entreprises;'
sudo -u postgres psql -d hauqe_certif -c \
  'SELECT count(*) AS documents FROM documents;'
find uploads/private -type f | wc -l
find app/uploads/avatars -type f | wc -l
```

Vérifier aussi le nombre de rôles, quelques comptes, des certifications et les documents d'une collecte. La présence d'une ligne en base ne prouve pas que son fichier est présent : ouvrir et télécharger plusieurs documents de test lors de la recette. Les chemins de sauvegarde historiques stockés dans la base peuvent encore contenir l'ancien chemin absolu ; s'ils diffèrent du nouveau, traiter ce point avant d'utiliser l'interface de restauration.

## 8. Premier démarrage local, sans Nginx ni service systemd

L'ancien serveur doit être arrêté. Depuis le nouveau serveur, démarrer **un seul** Uvicorn au premier plan sous le compte applicatif :

```bash
cd /var/www/api_hauqe
sudo -u sngsc .venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8014 --workers 1
```

Dans un second terminal SSH :

```bash
curl -fsS http://127.0.0.1:8014/api/v1/health
curl -I http://127.0.0.1:8014/
```

Ce démarrage lance aussi les traitements en arrière-plan, y compris la file SMTP. Vérifier les journaux, puis arrêter Uvicorn au premier plan avec `Ctrl+C` **avant** d'installer/démarrer `sngsc.service`. Pour tester l'interface depuis son poste sans Nginx, utiliser temporairement un tunnel SSH (`ssh -L 8014:127.0.0.1:8014 UTILISATEUR@HOTE`), puis ouvrir `http://127.0.0.1:8014/` sur le poste. Ne pas exposer le port 8014 au public.

Tester au minimum : connexion avec un compte restauré, MFA, lecture d'une entreprise et d'une certification, téléchargement d'une preuve, avatar, notifications et état des échéances. **Ne pas déclencher d'envoi SMTP de test vers des utilisateurs réels sans l'avoir prévu dans la fenêtre de maintenance.**

## 9. Installer le service, Nginx et HTTPS

Après arrêt du lancement manuel et validation locale :

```bash
cd /var/www/api_hauqe
sudo install -o root -g root -m 644 installation/sngsc.service \
  /etc/systemd/system/sngsc.service
sudo systemctl daemon-reload
sudo systemctl enable --now sngsc
sudo systemctl status sngsc --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
```

Le service doit utiliser `--workers 1` : son cycle FastAPI contient déjà le worker SMTP/sauvegardes. Ne pas lancer `python -m app.tasks.run_background_services` en parallèle.

Le modèle `installation/nginx-hauqe-certif.conf.example` publie l'application **à la racine du domaine**. Remplacer `DOMAINE_SNGSC`, installer le fichier Nginx selon la distribution, activer le site, puis :

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -I http://DOMAINE_SNGSC/
```

Configurer l'enregistrement DNS `A` vers la **nouvelle** adresse IP. Installer un certificat TLS (par exemple Certbot pour Nginx), vérifier `https://DOMAINE_SNGSC/`, puis corriger dans `.env` les deux URL publiques et redémarrer `sngsc`. Si l'application doit rester sous un préfixe `/sngsc/` plutôt qu'à la racine, ne pas réutiliser le modèle Nginx tel quel : vérifier séparément les routes frontend, `/api/v1`, `/static` et les liens des courriels.

Ne rendre publics que SSH, HTTP et HTTPS. PostgreSQL 5432 et Uvicorn 8014 restent accessibles localement seulement. Nginx ne doit pas servir directement `uploads`, `backups` ou `logs`.

## 10. Validation et retour arrière

Contrôles après bascule :

```bash
systemctl is-active sngsc
systemctl is-enabled sngsc
sudo journalctl -u sngsc -n 100 --no-pager
curl -fsS http://127.0.0.1:8014/api/v1/health
curl -I https://DOMAINE_SNGSC/
```

Effectuer ensuite une recette avec un compte restauré : connexion/MFA, collecte et documents, vérification, alertes et échéances, prévisualisation d'un rapport, courriel contrôlé, téléchargement d'une preuve et consultation des sauvegardes. Prévoir une sauvegarde complète **sur le nouveau serveur** et tester réellement sa restauration dans un environnement isolé. Garder les archives de transfert protégées jusqu'à validation, puis appliquer la politique de rétention retenue par la HAUQE.

Si la recette échoue avant ouverture au public : arrêter le nouveau service, conserver les journaux et les archives, analyser la cause. Pour revenir à l'ancien serveur, vérifier d'abord qu'aucune nouvelle donnée n'a été créée sur le nouveau ; sinon, un retour arrière sans rapprochement perdrait ces écritures. Ne jamais redémarrer les deux instances simultanément avec les mêmes courriels en attente.

**Base PostgreSQL modifiée sur le nouveau serveur : oui** — création de la base, restauration complète, puis migrations Alembic éventuelles. **Base de l'ancien serveur : aucune migration requise par ce guide.**
