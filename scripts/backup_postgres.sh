#!/usr/bin/env bash
# scripts/backup_postgres.sh — Automated PostgreSQL backup for UniConnect
# Usage: ./scripts/backup_postgres.sh [optional_output_dir]

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="${DB_CONTAINER:-uniconnect-prod-db-1}"
DB_USER="${POSTGRES_USER:-uniconnect}"
DB_NAME="${POSTGRES_DB:-uniconnect}"
BACKUP_FILE="${BACKUP_DIR}/uniconnect_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[UniConnect Backup] Starting PostgreSQL backup from container '${CONTAINER_NAME}'..."

docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-uniconnect_dev_pwd}" "${CONTAINER_NAME}" \
    pg_dump -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --no-owner --no-privileges | gzip > "${BACKUP_FILE}"

FILE_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
echo "[UniConnect Backup] Backup completed successfully: ${BACKUP_FILE} (${FILE_SIZE})"

# Retention: Remove backups older than 14 days
find "${BACKUP_DIR}" -name "uniconnect_backup_*.sql.gz" -type f -mtime +14 -delete
echo "[UniConnect Backup] Retention policy applied (purged archives older than 14 days)."
