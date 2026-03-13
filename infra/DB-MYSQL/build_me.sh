#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-mysql-imdb:8.0}"

mkdir -p "${SCRIPT_DIR}"

cat > "${SCRIPT_DIR}/Dockerfile" <<'DOCKERFILE'
FROM mysql:8.0
ENV MYSQL_ROOT_PASSWORD=YourStrong!Passw0rd
ENV MYSQL_DATABASE=imdb
DOCKERFILE

docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

echo "Built image: ${IMAGE_NAME}"