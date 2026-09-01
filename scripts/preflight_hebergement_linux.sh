#!/usr/bin/env bash
# Contrôle non destructif avant déploiement Linux de HAUQE Certif.
# À lancer depuis /var/www/api_hauqe, avec l'utilisateur qui déploie.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_USER="${SNGSC_APP_USER:-sngsc}"
EXPECTED_HEAD="c8f6a0b3d425"
FAILURES=0

ok() { printf 'OK    %s\n' "$1"; }
warn() { printf 'WARN  %s\n' "$1"; }
fail() { printf 'ECHEC %s\n' "$1"; FAILURES=$((FAILURES + 1)); }

require_command() {
  if command -v "$1" >/dev/null 2>&1; then ok "commande $1 disponible"; else fail "commande $1 introuvable"; fi
}

cd "$ROOT_DIR"
printf 'Précontrôle d’hébergement — %s\n\n' "$ROOT_DIR"

for command in python3 pg_dump pg_restore systemctl; do require_command "$command"; done

if [[ -x .venv/bin/python ]]; then
  ok "environnement virtuel présent"
else
  fail ".venv/bin/python absent ou non exécutable"
fi

if [[ -f .env ]]; then
  ok "fichier .env présent"
  for variable in DATABASE_URL SECRET_KEY MFA_FERNET_KEY HAUQE_SMTP_HOST HAUQE_SMTP_USER HAUQE_SMTP_PASSWORD HAUQE_SMTP_FROM; do
    if grep -qE "^${variable}=.+" .env && ! grep -qE "^${variable}=CHANGE_ME" .env; then
      ok "variable $variable renseignée"
    else
      fail "variable $variable absente ou fictive dans .env"
    fi
  done
else
  fail "fichier .env absent"
fi

for directory in logs backups uploads uploads/private app/uploads/avatars; do
  if [[ -d "$directory" ]]; then
    ok "répertoire $directory présent"
  else
    fail "répertoire $directory absent"
  fi
done

if id "$APP_USER" >/dev/null 2>&1; then
  ok "compte système $APP_USER présent"
  for directory in logs backups uploads uploads/private app/uploads/avatars; do
    if sudo -u "$APP_USER" test -w "$ROOT_DIR/$directory"; then
      ok "$APP_USER peut écrire dans $directory"
    else
      fail "$APP_USER ne peut pas écrire dans $directory"
    fi
  done
else
  fail "compte système $APP_USER absent"
fi

if [[ -x .venv/bin/alembic ]]; then
  HEADS="$(./.venv/bin/alembic heads 2>&1 || true)"
  CURRENT="$(./.venv/bin/alembic current 2>&1 || true)"
  if grep -q "$EXPECTED_HEAD" <<<"$HEADS"; then ok "tête Alembic attendue : $EXPECTED_HEAD"; else fail "tête Alembic inattendue : $HEADS"; fi
  if grep -q "$EXPECTED_HEAD" <<<"$CURRENT"; then ok "base alignée sur $EXPECTED_HEAD"; else fail "base non alignée : $CURRENT"; fi
else
  fail "alembic absent du venv"
fi

if systemctl is-active --quiet sngsc; then ok "service sngsc actif"; else warn "service sngsc inactif : normal avant le redémarrage final"; fi

AVAILABLE_KB="$(df -Pk "$ROOT_DIR" | awk 'NR==2 {print $4}')"
if [[ -n "$AVAILABLE_KB" && "$AVAILABLE_KB" -ge 5242880 ]]; then
  ok "espace disque disponible : $((AVAILABLE_KB / 1024)) MiB"
else
  fail "moins de 5 GiB disponibles pour les sauvegardes et téléversements"
fi

printf '\nRésultat : '
if [[ "$FAILURES" -eq 0 ]]; then
  printf 'PRÊT POUR LE DÉPLOIEMENT.\n'
else
  printf '%s contrôle(s) bloquant(s) à corriger avant le déploiement.\n' "$FAILURES"
  exit 1
fi
