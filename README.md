# rag-chat-sample

Azure AI Foundry Agent を Streamlit UI から操作するサンプルです。ログイン付きのシンプルなチャット画面を提供し、Azure AI Project と接続して回答を生成します。

![チャットUIのスクリーンショット](images/app.png)

## 必要な環境

- Python3.10 以降
- `pip install -r requirements.txt` で依存を導入
- `.env_template` を `.env` にコピーして以下の値を設定（ローカル実行・デプロイ共通）
  - `APP_LOGIN_USERNAME` / `APP_LOGIN_PASSWORD`: Streamlit ログイン用の認証情報
  - `AZURE_AI_PROJECT_ENDPOINT`: 接続先 Azure AI Project のエンドポイント URL
  - `AZURE_AI_AGENT_NAME`: 呼び出すエージェント名

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows は .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Azure App Service へのデプロイ

前提として Azure Portal 側で App Service を作成し、`.env`に必要な値を設定しておきます。`scripts/startup.sh`はデフォルトで`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`を実行する想定です。必要に応じて修正してください。

### Linux / macOS: `scripts/deploy.sh`

1. `scripts/deploy.sh` の先頭で定義している `RG` / `LOC` / `WEBAPP` を自分の環境に合わせて変更
2. 実行権限を付与してシェルから実行

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Windows: `scripts/deploy.ps1`

1. PowerShell で`scripts/deploy.ps1`を開き、`$RG` / `$Loc` / `$WebApp`を自分のリソース名に合わせる
2. 必要であれば実行ポリシーを緩和し、PowerShell（推奨: PowerShell 7/pwsh）から実行

```powershell
pwsh -File scripts/deploy.ps1
# または Windows PowerShell:
powershell.exe -ExecutionPolicy Bypass -File scripts\deploy.ps1
```

### 両スクリプトが実行する内容

- `.env` の読み込みと必須値チェック
- リポジトリを `deploy.zip` に圧縮
- `az login`（未ログイン時）
- App Service のアプリ設定更新
  - `APP_LOGIN_USERNAME`, `APP_LOGIN_PASSWORD`
  - `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_AGENT_NAME`
  - `SCM_DO_BUILD_DURING_DEPLOYMENT`, `WEBSITES_PORT`
- スタートアップコマンド（`bash scripts/startup.sh`）の設定
- `az webapp deploy`による Zip Deploy

両スクリプトともログ出力とエラーメッセージは日本語化済みです。必要に応じて `.env` の値や `scripts/deploy.*` 内の設定を変更してご利用ください。
