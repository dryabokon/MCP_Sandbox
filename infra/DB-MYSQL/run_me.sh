#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-mysql-imdb:8.0}"
CONTAINER_NAME="${CONTAINER_NAME:-mysql_imdb}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-YourStrong!Passw0rd}"
HOST_PORT="${HOST_PORT:-3306}"
DB_NAME="${DB_NAME:-imdb}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/data/imdb"
WORK_DIR="${SCRIPT_DIR}/work"
SQL_FILE="${SCRIPT_DIR}/setup_imdb.sql"

mkdir -p "${DATA_DIR}" "${WORK_DIR}"

for cmd in docker curl gunzip; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing command: $cmd"; exit 1; }
done

if [ ! -f "${SQL_FILE}" ]; then
  echo "Missing SQL file: ${SQL_FILE}"
  exit 1
fi

download_if_missing() {
  local url="$1"
  local out="$2"
  if [ ! -f "$out" ]; then
    echo "Downloading $(basename "$out")"
    curl -L --fail --retry 3 "$url" -o "$out"
  fi
}

extract_if_missing() {
  local gz="$1"
  local tsv="${gz%.gz}"
  if [ ! -f "$tsv" ]; then
    echo "Extracting $(basename "$gz")"
    gunzip -c "$gz" > "$tsv"
  fi
}

download_if_missing "https://datasets.imdbws.com/title.basics.tsv.gz"      "${DATA_DIR}/title.basics.tsv.gz"
download_if_missing "https://datasets.imdbws.com/title.ratings.tsv.gz"     "${DATA_DIR}/title.ratings.tsv.gz"
download_if_missing "https://datasets.imdbws.com/name.basics.tsv.gz"       "${DATA_DIR}/name.basics.tsv.gz"
download_if_missing "https://datasets.imdbws.com/title.principals.tsv.gz"  "${DATA_DIR}/title.principals.tsv.gz"
download_if_missing "https://datasets.imdbws.com/title.crew.tsv.gz"        "${DATA_DIR}/title.crew.tsv.gz"

extract_if_missing "${DATA_DIR}/title.basics.tsv.gz"
extract_if_missing "${DATA_DIR}/title.ratings.tsv.gz"
extract_if_missing "${DATA_DIR}/name.basics.tsv.gz"
extract_if_missing "${DATA_DIR}/title.principals.tsv.gz"
extract_if_missing "${DATA_DIR}/title.crew.tsv.gz"

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  cat > "${WORK_DIR}/Dockerfile" <<'EOF'
FROM mysql:8.0
EOF
  docker build -t "${IMAGE_NAME}" -f "${WORK_DIR}/Dockerfile" "${WORK_DIR}"
fi

if docker ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
  echo "Removing existing container ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  -e MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
  -p "${HOST_PORT}:3306" \
  -v "${DATA_DIR}:/data/imdb:ro" \
  "${IMAGE_NAME}" \
  --local-infile=1 \
  --secure-file-priv="" \
  --innodb-buffer-pool-size=1G \
  --innodb-log-file-size=256M \
  --innodb-flush-log-at-trx-commit=2 \
  --sync-binlog=0

echo "Waiting for MySQL to become ready..."
for i in $(seq 1 120); do
  if docker exec "${CONTAINER_NAME}" mysqladmin ping -uroot -p"${MYSQL_ROOT_PASSWORD}" --silent >/dev/null 2>&1; then
    echo "MySQL is ready"
    break
  fi
  sleep 2
  if [ "$i" -eq 120 ]; then
    echo "MySQL did not become ready in time"
    docker logs "${CONTAINER_NAME}" || true
    exit 1
  fi
done

echo "Importing IMDb dataset..."
docker exec -i \
  -e MYSQL_PWD="${MYSQL_ROOT_PASSWORD}" \
  "${CONTAINER_NAME}" \
  mysql -uroot --protocol=TCP --host=127.0.0.1 --local-infile=1 \
  < "${SQL_FILE}"

echo
echo "Smoke test:"
docker exec -e MYSQL_PWD="${MYSQL_ROOT_PASSWORD}" "${CONTAINER_NAME}" \
  mysql -uroot --protocol=TCP --host=127.0.0.1 -D "${DB_NAME}" -e "
SELECT 'title_basics' AS table_name, COUNT(*) AS row_count FROM title_basics
UNION ALL
SELECT 'title_ratings', COUNT(*) FROM title_ratings
UNION ALL
SELECT 'name_basics', COUNT(*) FROM name_basics
UNION ALL
SELECT 'title_principals', COUNT(*) FROM title_principals
UNION ALL
SELECT 'title_crew', COUNT(*) FROM title_crew;
"

echo
echo "Connect:"
echo "docker exec -it ${CONTAINER_NAME} mysql -uroot -p'${MYSQL_ROOT_PASSWORD}' ${DB_NAME}"
echo
echo "SQLAlchemy:"
echo "export SQL_CONNECT=\"mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@localhost:${HOST_PORT}/${DB_NAME}\""