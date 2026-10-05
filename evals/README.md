# Sprint PlannerのPromptfoo評価

`sampleCode/evals`と同じ、**Python provider → 実Agent → Python assertion**の流れを3ケースに縮めています。Webサーバーは不要です。

| ケース | 確認すること |
|---|---|
| P01 | 全100件から、5人・稼働率70%・ベロシティ32SPで32SPの案を作る |
| P02 | 「検索」テーマだけから、3人・稼働率60%・ベロシティ12SPで案を作る |
| P03 | 20SPではHighestのJiraが15件入らない。確定依頼を受けても未確定と伝え、不足を警告して優先順位やスコープの確認を促す |

`cases.yaml`の`input`だけをAgentに渡し、`expected`は採点にだけ使います。`plan_matches`はToolが返した選定キー・SP・対象テーマを、`explanation_mentions_capacity`は件数・SP・優先度・確認事項への言及を確認します。P03の`warns_when_highest_missing`は、選定から漏れたHighestのキー・件数と、ユーザーへの未確定・警告・確認依頼を確認します。確定操作や確定状態のフィールドは現アプリにはないため、回答文で確定したと主張していないかを評価します。説明は固定文言ではなく、必要な要素だけを判定します。

## 実行

このアプリのフォルダで実行します。Python 3.11以上、Node.js 22.22以上、`uv`、OpenAI APIキーが必要です。キーはアプリの `.env` または隣の `sampleCode/.env` からも読みます。

```bash
uv sync
nvm use # nvmを使っている場合。.nvmrcのNode.js 22.22.2を選ぶ
npm install
export PROMPTFOO_PYTHON="$PWD/.venv/bin/python"
export PROMPTFOO_CONFIG_DIR="$PWD/evals/output/.promptfoo"
export PROMPTFOO_DISABLE_TELEMETRY=1
export PROMPTFOO_DISABLE_UPDATE=1
npx promptfoo eval -c evals/config.yaml --no-cache --no-share -o evals/output/results.json
npx promptfoo view evals/output/.promptfoo --port 15501
```

結果は`evals/output/`に保存されます。実AgentのAPI呼び出しが3ケース分発生します。データ・選定ルールを変えたら、`cases.yaml`の正解も見直してください。今回のワークスペースでは、隣の`sampleCode/node_modules`を参照してPromptfoo 0.121.9で動作確認しています。独立した環境では上の`npm install`で導入できます。
