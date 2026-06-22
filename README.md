# self-dialog-bot

2つの役割を持つAIが、最初の質問への回答と、その回答を深掘りする質問を交互に生成する小さなPythonアプリです。API呼び出しとトークン・料金集計は `self_dialogue_core.py` に集約し、CLIとStreamlit UIの両方から利用します。

## セットアップ

Python 3.11以上が必要です。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

`.env` の `OPENAI_API_KEY` に自分のキーを設定してください。キーや `.env` はコミットしないでください。

## 実行

CLI:

```bash
self-dialog "幸福とは何か？" --rounds 3 --max-tokens 5000 --max-usd 0.01
```

Web UI:

```bash
streamlit run streamlit_app.py
```

現在、料金計算を保証するモデルは `gpt-4.1-nano` です。トークン・料金上限はAPIレスポンス受信後に判定するため、最後の1リクエスト分だけ上限を超える場合があります。APIエラー、空の応答、usage欠落時は処理を中断し、誤った集計結果を返しません。

## 開発・検証

すべてのテストはOpenAIクライアントをモックし、実APIを呼びません。

```bash
ruff check .
pytest
python -m compileall -q cli.py self_dialogue_core.py streamlit_app.py tests
```
