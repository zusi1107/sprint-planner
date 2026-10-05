"""PromptfooのPython provider。実Webアプリと同じchat()を1ターン実行する。"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import ChatRequest, chat


async def call_api(prompt, options, context):
    case = context["vars"]
    # expectedは採点専用。Agentにはinputのみ渡す。
    body = ChatRequest(**case["input"])
    try:
        result = await chat(body)
    except Exception as exc:
        # API障害は不合格ではなくprovider errorとして表示する。
        return {"error": f"{case['case_id']}: {type(exc).__name__} (HTTP {getattr(exc, 'status_code', '-')})"}
    return {
        "output": json.dumps(result, ensure_ascii=False),
        "metadata": {"case_id": case["case_id"], "model": os.getenv("OPENAI_MODEL", "gpt-6-luna")},
    }
