#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ "${1:-}" != "--yes" ]]; then
  read -r -p "Hapus data dummy? Data asli dipertahankan. [y/N] " jawab
  case "$jawab" in
    y|Y|yes|YES|Ya|ya) ;;
    *) echo "Dibatalkan."; exit 0 ;;
  esac
fi

docker compose exec -T web python -m scripts.clear_dummy
