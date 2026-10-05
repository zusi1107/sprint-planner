"""FastAPI + Responses API の最小構成スプリントプランニングAgent。"""

import json
import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from backlog import BACKLOG
from planner import capacity, draft_sprint

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
if not os.getenv("OPENAI_API_KEY"):
    # 同じワークスペースの教材キーを再利用。値を複製・画面表示しない。
    sample_key = dotenv_values(ROOT.parent / "sampleCode" / ".env").get("OPENAI_API_KEY")
    if sample_key:
        os.environ["OPENAI_API_KEY"] = sample_key
app = FastAPI(title="Sprint Planner")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

INSTRUCTIONS = """あなたはプロダクトマネージャを支援するスプリントプランニングAgentです。
回答は日本語で、簡潔かつ具体的にしてください。計画作成の依頼では必ず draft_sprint を呼び、
返されたタスクとSPだけを提案してください。バックログについて聞かれたら get_backlog を呼んでください。
Toolが返した内容を事実として扱い、存在しないタスクや依存関係を作らないでください。
計画を提案するときは採用件数、合計SP、上限SP、優先順位の根拠、確認すべき点を3〜5文で述べてください。
タスク一覧は別のカードに表示されるため、回答に全件を列挙したりMarkdownの表や見出しを作ったりしないでください。
これは架空データであり、見積もりや依存関係はチームで確認する前提です。"""

TOOLS = [
    {
        "type": "function", "name": "get_backlog",
        "description": "架空のJiraバックログ100件を取得する。個別タスクや優先度の質問に使う。",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function", "name": "draft_sprint",
        "description": "現在のチームリソースと優先度から、2週間スプリントの候補を作る。focusは特定テーマを優先したい場合だけ指定する。",
        "parameters": {
            "type": "object",
            "properties": {"focus": {"type": "string", "description": "例: 検索。全件から選ぶ場合は空文字。"}},
            "required": ["focus"], "additionalProperties": False,
        },
    },
]


class Message(BaseModel):
    role: str
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[Message] = Field(default_factory=list, max_length=12)
    members: int = Field(default=5, ge=1, le=30)
    availability: float = Field(default=0.7, ge=0.1, le=1)
    velocity: int = Field(default=32, ge=1, le=300)


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/bootstrap")
def bootstrap():
    return {"backlog": BACKLOG, "key_configured": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/api/chat")
async def chat(body: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY を .env に設定してください。")

    # ブラウザーからの履歴は発話のみ受け付け、Tool実行やsystem指示は受け取らない。
    history = [
        {"role": item.role, "content": item.content}
        for item in body.history[-12:]
        if item.role in {"user", "assistant"}
    ]
    history.append({"role": "user", "content": body.message})
    resource_context = (
        f"チーム人数: {body.members}人、2週間: 10稼働日、稼働率: {body.availability:.0%}、"
        f"直近ベロシティ: {body.velocity}SP、今回の上限: "
        f"{capacity(body.members, body.availability, body.velocity)}SP。"
    )
    plan = None
    try:
        async with AsyncOpenAI(timeout=60, max_retries=0) as client:
            for _ in range(4):
                response = await client.responses.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
                    instructions=INSTRUCTIONS + "\n" + resource_context,
                    input=history,
                    tools=TOOLS,
                    parallel_tool_calls=False,
                    store=False,
                    include=["reasoning.encrypted_content"],
                    max_output_tokens=2500,
                )
                if response.status != "completed":
                    raise RuntimeError(f"AIの応答が完了しませんでした: {response.status}")
                for item in response.output:
                    history.append(item.model_dump(exclude_none=True))
                calls = [item for item in response.output if item.type == "function_call"]
                if not calls:
                    return {"reply": response.output_text, "plan": plan}
                for call in calls:
                    args = json.loads(call.arguments or "{}")
                    if call.name == "get_backlog":
                        result = BACKLOG
                    elif call.name == "draft_sprint":
                        plan = draft_sprint(body.members, body.availability, body.velocity, str(args.get("focus", ""))[:30])
                        result = plan
                    else:
                        result = {"error": "Unknown tool"}
                    history.append({
                        "type": "function_call_output", "call_id": call.call_id,
                        "output": json.dumps(result, ensure_ascii=False),
                    })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI呼び出しに失敗しました: {exc}") from exc
    raise HTTPException(status_code=502, detail="Tool呼び出しの上限に達しました。")
