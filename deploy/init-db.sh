#!/bin/sh
# Sourced by the official postgres image only on first initialization.
set -eu
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    --set=ON_ERROR_STOP=1 --set=app_password="$HAUQE_DB_APP_PASSWORD" <<'SQL'
CREATE ROLE hauqe_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'app_password';
GRANT CONNECT ON DATABASE hauqe_certif TO hauqe_app;
GRANT USAGE, CREATE ON SCHEMA public TO hauqe_app;
SQL
