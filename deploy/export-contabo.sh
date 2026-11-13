#!/bin/sh
# Read-only source export. Run on Contabo as root, not on Windows.
set -eu
umask 077
if [ "$(id -u)" -ne 0 ]; then echo 'Run as root (or sudo).' >&2; exit 1; fi
db_name=${1:-hauqe_certif}
case "$db_name" in ''|*[!a-zA-Z0-9_]*) echo 'Invalid database name.' >&2; exit 1;; esac
source_dir=/var/www/api_hauqe
test -d "$source_dir/uploads" || { echo 'Source uploads directory missing.' >&2; exit 1; }
command -v pg_dump >/dev/null
command -v pg_restore >/dev/null
command -v runuser >/dev/null
mkdir -p /var/backups/sngsc-transfer
destination=$(mktemp -d /var/backups/sngsc-transfer/export-XXXXXXXX)
printf 'Export directory: %s\n' "$destination"
runuser -u postgres -- psql -X -At -d "$db_name" -c 'SELECT version();' > "$destination/source-version.txt"
runuser -u postgres -- psql -X -At -d "$db_name" -c 'SELECT version_num FROM public.alembic_version;' > "$destination/alembic-version.txt"
runuser -u postgres -- pg_dump -Fc -d "$db_name" > "$destination/database.dump"
pg_restore --list "$destination/database.dump" > "$destination/catalogue.txt"
for required in app alembic alembic.ini requirements.txt; do
    test -e "$source_dir/$required" || { echo "Missing application component: $required" >&2; exit 1; }
done
tar --exclude='app/uploads' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.env*' --exclude='*.pem' --exclude='*.key' \
    -czf "$destination/application.tar.gz" -C "$source_dir" \
    app alembic alembic.ini requirements.txt
if [ -d "$source_dir/app/uploads/avatars" ]; then
    tar -czf "$destination/files.tar.gz" -C "$source_dir" uploads app/uploads/avatars
else
    tar -czf "$destination/files.tar.gz" -C "$source_dir" uploads
fi
runuser -u postgres -- psql -X -At -d "$db_name" -c "SELECT 'utilisateurs',count(*) FROM utilisateurs UNION ALL SELECT 'entreprises',count(*) FROM entreprises UNION ALL SELECT 'certifications',count(*) FROM certifications;" > "$destination/counts.txt"
(
    cd "$destination"
    sha256sum database.dump application.tar.gz files.tar.gz source-version.txt alembic-version.txt counts.txt > SHA256SUMS
)
printf 'Export finished. Check warnings, restore-test, and transfer securely: %s\n' "$destination"
printf 'No .env or encryption keys included. A live export is not a synchronized final cutover.\n'
