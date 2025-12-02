#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

RG="tmp"
LOC="japaneast"
WEBAPP="tmp-rag-chat"
ZIP="$ROOT_DIR/deploy.zip"

ENV_FILE="$ROOT_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[エラー] $ENV_FILE がありません。必要な設定を記入して作成してください。" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

required_vars=(
  APP_LOGIN_USERNAME
  APP_LOGIN_PASSWORD
  AZURE_AI_PROJECT_ENDPOINT
  AZURE_AI_AGENT_NAME
)

for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "[エラー] $var が $ENV_FILE に設定されていません。" >&2
    exit 1
  fi
done

echo "[情報] $ZIP にパッケージングします"
rm -f "$ZIP"
zip -r "$ZIP" . \
  -x '.git/*' '.venv/*' '__pycache__/*' '*.pyc' '.azure/*' '.env' \
  -x 'README.md' '.vscode/*'

if ! az account show >/dev/null 2>&1; then
  echo "[情報] az login を実行します"
  az login >/dev/null
fi

echo "[情報] App Service のアプリ設定を更新します"
az webapp config appsettings set \
  --resource-group "$RG" \
  --name "$WEBAPP" \
  --settings \
    APP_LOGIN_USERNAME="$APP_LOGIN_USERNAME" \
    APP_LOGIN_PASSWORD="$APP_LOGIN_PASSWORD" \
    AZURE_AI_PROJECT_ENDPOINT="$AZURE_AI_PROJECT_ENDPOINT" \
    AZURE_AI_AGENT_NAME="$AZURE_AI_AGENT_NAME" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
    WEBSITES_PORT="8000"

STARTUP_CMD='bash scripts/startup.sh'
echo "[情報] スタートアップコマンドを $STARTUP_CMD に設定します"
az webapp config set --resource-group "$RG" --name "$WEBAPP" --startup-file "$STARTUP_CMD"

echo "[情報] $ZIP を $WEBAPP にデプロイします"
az webapp deploy --resource-group "$RG" --name "$WEBAPP" --type zip --src-path "$ZIP"

echo "[情報] デプロイ完了"
