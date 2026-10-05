# Sprint Planner ハンズオン

`sampleCode` の Responses API + FastAPI の構成を参考にした、プロダクトマネージャ向けの小さなチャットアプリです。架空のJiraバックログ100件から、チーム人数・稼働率・直近ベロシティを使って、次の2週間スプリント案を作ります。Jiraへの接続や書き込みはありません。

## 起動

Python 3.11以上と `uv` が必要です。このフォルダで実行してください。

```bash
uv sync
uv run uvicorn app:app --host 127.0.0.1 --port 8767
```

ブラウザーで http://127.0.0.1:8767/ を開き、「スプリント案を作成」を押します。APIキーは新アプリの環境変数または `.env` を優先し、未設定なら隣の `sampleCode/.env` を読みます。独立して使う場合は `cp .env.example .env` の後、`.env` に `OPENAI_API_KEY` を設定してください。

## 読む順番

1. `backlog.py` — 100件のモックデータ
2. `planner.py` — SP上限と優先度を守る計画Tool
3. `app.py` — `chat()` の Responses API / Tool 呼び出しループ
4. `static/` — チャットとバックログ表示
5. `evals/` — Promptfooで実Agentを評価する2ケース（[実行手順](evals/README.md)）

計画は優先度順、同順位では小さいSP順に詰めます。SP上限は「直近ベロシティ」と「人数 × 10日 × 稼働率」の小さい方です。1稼働日=1SPは演習用の仮定です。依存関係・担当者割当・Jira連携はまだ扱いません。AI APIの利用料は発生します。
