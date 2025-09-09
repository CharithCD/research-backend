#!/usr/bin/env sh
set -euo pipefail

MODEL_DIR="/app/app/model"
mkdir -p "$MODEL_DIR"

: "${SPACES_KEY:?SPACES_KEY not set}"
: "${SPACES_SECRET:?SPACES_SECRET not set}"
: "${SPACES_REGION:?SPACES_REGION not set}"
: "${SPACES_BUCKET:?SPACES_BUCKET not set}"
: "${SPACES_PREFIX:?SPACES_PREFIX not set}"

CONFIG_FILE="/tmp/s3cfg"
cat > "$CONFIG_FILE" <<EOF
[default]
access_key = $SPACES_KEY
secret_key = $SPACES_SECRET
host_base = ${SPACES_REGION}.digitaloceanspaces.com
host_bucket = %(bucket)s.${SPACES_REGION}.digitaloceanspaces.com
bucket_location = $SPACES_REGION
use_https = True
signature_v2 = False
EOF

copy_if_missing() {
  key="$1"
  dest="$MODEL_DIR/$1"
  if [ ! -s "$dest" ]; then
    echo "→ fetching $key"
    s3cmd -c "$CONFIG_FILE" get "s3://$SPACES_BUCKET/$SPACES_PREFIX/$key" "$dest"
  else
    echo "✓ $key present; skip"
  fi
}

copy_if_missing config.json
copy_if_missing preprocessor_config.json
copy_if_missing vocab.json
copy_if_missing model.safetensors

echo "[bootstrap] done."
