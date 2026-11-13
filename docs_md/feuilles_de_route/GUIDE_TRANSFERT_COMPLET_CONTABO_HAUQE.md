# Transfert complet Contabo → HAUQE, indépendant de Docker

> Exigence de livraison confirmée : le projet remis à HAUQE doit être Dockerisé.
> L'indépendance de Docker concerne uniquement l'export de la source Contabo,
> pas le format final d'installation HAUQE. Ce guide décrit la sauvegarde ;
> compléter obligatoirement par GUIDE_LIVRAISON_DOCKER_HAUQE.md pour la livraison.

## Objectif

Livrer la version réellement exploitée sur Contabo, ses données et ses fichiers.
Docker est requis à destination, mais n'est pas un préalable à l'export de la
production existante. Ne pas remplacer le code Contabo pour exporter.

## Paquet à remettre

- database.dump : tables, comptes SNGSC, rôles applicatifs, historiques et données.
- application.tar.gz : app (Python, HTML, CSS, JavaScript, logo), alembic,
  alembic.ini et requirements.txt de la production Contabo.
- files.tar.gz : uploads et, s'il existe, app/uploads/avatars.
- source-version.txt, alembic-version.txt, counts.txt, catalogue.txt et SHA256SUMS.
- Configuration et clés nécessaires fournies séparément par canal sécurisé.

Le script exclut le .env, les clés PEM/KEY, le venv, Git et les caches Python
de l'archive applicative. Le venv sera recréé à destination. Il n'est pas garanti
que tous les secrets possibles soient reconnus par leur extension : contrôler
les sources avant partage. Les fichiers privés uploadés font intentionnellement
partie du paquet de données protégé. Inventorier les pièces stockées ailleurs,
stockages externes, liens symboliques et personnalisations hors app : ils ne
sont pas automatiquement capturés. Ne pas considérer l'export comme exhaustif
avant cet inventaire et les tests de téléchargement.

## Export sur Contabo

Transférer seulement deploy/export-contabo.sh depuis Windows vers un dossier
administratif du serveur via SFTP/SCP, sans pull dans la production.
Ne pas réutiliser la vieille copie du script si elle ne contient pas l'archive
application.tar.gz. Garder les fins de ligne LF.

Sur Contabo, valider le nom de base et contrôler le script avant lancement :

```bash
sh -n /chemin/vers/export-contabo.sh
sudo sh /chemin/vers/export-contabo.sh hauqe_certif
```

Le script lit `/var/www/api_hauqe` et crée un dossier privé unique sous
`/var/backups/sngsc-transfer`. Il ne modifie ni le code, ni la base source, ni
les services. Si erreur, ne pas utiliser le paquet incomplet. Il nécessite
les clients PostgreSQL compatibles avec la source et l'accès système postgres.
Le dump ne crée pas les comptes SQL globaux : à gérer côté destination.

Un premier export peut être fait à chaud pour répéter l'installation. Pour le
transfert final cohérent, convenir d'une fenêtre sans saisie et arrêter les
processus d'écriture, worker et tâches planifiées identifiés, puis refaire
l'export. Ne pas appliquer des noms de services supposés sans vérification.

## Transport et secrets

Télécharger/transférer le dossier complet par SFTP/SCP ou autre canal chiffré
restreint. Ne pas joindre un dump de production à un dépôt Git ou lien public.
Fournir à l'informaticien autorisé la configuration source pertinente, clés
SECRET_KEY/MFA_FERNET_KEY indispensables, sans diffuser les secrets dans le chat.
Les paramètres base, domaine et SMTP seront adaptés à HAUQE. Conserver les clés
historiques nécessaires pour lire les données chiffrées ; ne pas en inventer de nouvelles.

## Restauration par l'informaticien

1. Vérifier `sha256sum -c SHA256SUMS` dans le dossier reçu.
2. Vérifier version source PostgreSQL ; choisir une destination de même version
   majeure pour la première restauration, pas une version antérieure.
3. Restaurer l'application sur une destination neuve (pas un site existant).
   Le chemin `/var/www/api_hauqe` facilite la conservation des références Linux
   aux documents ; sinon prévoir un traitement contrôlé de ces chemins.
4. Créer un venv Python compatible puis installer les dépendances. Les fichiers
   historiques de production peuvent être incomplets : intégrer les corrections
   connues `sqlalchemy[asyncio]` et `argon2-cffi` et vérifier les imports avant démarrage.
5. Créer une base vide et un utilisateur SQL applicatif, distinct des comptes
   SNGSC en tables ; restaurer avec pg_restore --no-owner --no-privileges
   --single-transaction --exit-on-error vers cette cible explicitement nommée.
6. Restaurer files.tar.gz dans la nouvelle racine applicative et régler les droits
   du compte qui exécute le service. Ne pas extraire sur des fichiers nouveaux
   existants sans sauvegarde : l'extraction peut les remplacer.
7. Renseigner la configuration privée, conserver les clés source requises,
   adapter les connexions et liens publics, désactiver SMTP ET worker pendant les essais.
8. Comparer révision Alembic, nombres de comptes/entreprises/certifications ;
   tester connexion, MFA, preuves, pièces jointes, avatars et téléchargements.
9. Ne pas lancer migrations ou seeds à l'aveugle : comparer le schéma du dump
   et le code effectivement livré, puis déclarer chaque migration nécessaire.
10. Configurer service de démarrage, Nginx/HTTPS, sauvegardes hors serveur et
    tester une restauration. Réactiver un seul worker après bascule approuvée.

La procédure Docker détaillée, obligatoire pour la livraison HAUQE, est dans
[GUIDE_LIVRAISON_DOCKER_HAUQE.md](GUIDE_LIVRAISON_DOCKER_HAUQE.md).
Ne pas appliquer une migration de la nouvelle image au dump ancien sans examiner
les changements métier associés. L'archive application est le code Contabo,
pas automatiquement celui du poste Windows.

## Statut

Script et guide préparés localement, aucun export Contabo exécuté par l'assistant.
Le dump réel et les archives restent à générer sur le serveur, puis à tester.
Base PostgreSQL source modifiée : non. Migration nouvelle : aucune.
