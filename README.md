# rag-chat-sample

Azure AI Foundry Agent を Streamlit UI から操作するサンプルです。ログイン付きのシンプルなチャット画面を提供し、Azure AI Project と接続して回答を生成します。

## 必要な環境

- Python 3.10 以降
- `pip install -r requirements.txt` で依存を導入
- `.env` に以下の値を設定（ローカル実行・デプロイ共通）
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

ポータルで App Service を作成済みの場合、`scripts/deploy.sh` で Zip Deploy とアプリ設定更新をまとめて実行できます。

1. `scripts/startup.sh` にアプリ起動コマンドを記述（既定で `streamlit run app.py` を実行）
2. `scripts/deploy.sh` 冒頭の `RG` / `LOC` / `WEBAPP` などを自分のリソース名に合わせて編集
3. `.env` に上記 4 つの環境変数を設定
4. 実行権限を付与してデプロイ

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### deploy.sh が行うこと

- `.env` の読み込みと必須値チェック
- リポジトリを `deploy.zip` に圧縮
- `az login`（未ログイン時）
- App Service のアプリ設定更新
  - `APP_LOGIN_USERNAME`, `APP_LOGIN_PASSWORD`
  - `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_AGENT_NAME`
  - `SCM_DO_BUILD_DURING_DEPLOYMENT`, `WEBSITES_PORT`
- スタートアップコマンド（`bash scripts/startup.sh`）の設定
- `az webapp deploy` による Zip Deploy

ログ出力とエラーメッセージは日本語化済みです。必要に応じて `.env` の値や `scripts/deploy.sh` 内の設定を変更してご利用ください。
