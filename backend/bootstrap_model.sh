#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${MODEL_DIR:-/app/app/model}"
mkdir -p "$MODEL_DIR"

# If model already present, skip
if [ -f "$MODEL_DIR/config.json" ] || [ -f "$MODEL_DIR/preprocessor_config.json" ]; then
  echo "[bootstrap] Model already present in $MODEL_DIR – skip download."
  exit 0
fi

# Build a temp s3cmd config from env (no files committed)
TMP_CFG="/tmp/s3cfg"
cat > "$TMP_CFG" <<EOF
[default]
access_key = ${SPACES_KEY}
secret_key = ${SPACES_SECRET}
host_base = ${SPACES_ENDPOINT}
host_bucket = %(bucket)s.${SPACES_ENDPOINT}
use_https = True
signature_v2 = False
EOF

echo "[bootstrap] Syncing model from s3://${SPACES_BUCKET}/${SPACES_PREFIX} → ${MODEL_DIR}"
s3cmd -c "$TMP_CFG" sync "s3://${SPACES_BUCKET}/${SPACES_PREFIX}/" "${MODEL_DIR}/"
echo "[bootstrap] Done."
