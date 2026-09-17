#!/usr/bin/env bash
# scripts/restore_postgres.sh — Restore PostgreSQL database from backup archive
# Usage: ./scripts/restore_postgres.sh <path_to_backup_file.sql.gz>

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Error: Backup file path required."
    echo "Usage: $0 <path_to_backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER_NAME="${DB_CONTAINER:-uniconnect-prod-db-1}"
DB_USER="${POSTGRES_USER:-uniconnect}"
DB_NAME="${POSTGRES_DB:-uniconnect}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' not found."
    exit 1
fi

echo "[UniConnect Restore] WARNING: This will overwrite data in '${DB_NAME}'!"
echo "[UniConnect Restore] Restoring from '${BACKUP_FILE}' into container '${CONTAINER_NAME}'..."

gunzip -c "${BACKUP_FILE}" | docker exec -i -e PGPASSWORD="${POSTGRES_PASSWORD:-uniconnect_dev_pwd}" "${CONTAINER_NAME}" \
    psql -U "${DB_USER}" -d "${DB_NAME}"

echo "[UniConnect Restore] Database restoration completed successfully."
