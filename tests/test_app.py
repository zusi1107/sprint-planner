"""実APIを呼ばずに、Web入口とAgentのTool往復を確認する。"""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app
from backlog import BACKLOG


class FakeItem:
    type = "function_call"
    name = "draft_sprint"
    arguments = '{"focus":""}'
    call_id = "call_1"

    def model_dump(self, exclude_none=True):
        return {"type": self.type, "name": self.name, "arguments": self.arguments, "call_id": self.call_id}


class FakeOpenAI:
    def __init__(self, **kwargs):
        self.calls = 0
        self.responses = SimpleNamespace(create=self.create)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return SimpleNamespace(status="completed", output=[FakeItem()], output_text="")
        assert any(item.get("type") == "function_call_output" for item in kwargs["input"])
        return SimpleNamespace(status="completed", output=[], output_text="計画案を作成しました。")


class AppTest(unittest.TestCase):
    def test_bootstrap_has_100_unique_issues(self):
        response = TestClient(app).get("/api/bootstrap")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(BACKLOG), 100)
        self.assertEqual(len({issue["key"] for issue in response.json()["backlog"]}), 100)

    def test_agent_tool_round_trip_returns_plan_within_capacity(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("app.AsyncOpenAI", FakeOpenAI):
            response = TestClient(app).post("/api/chat", json={"message": "スプリント案を作って"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["reply"], "計画案を作成しました。")
        self.assertEqual(data["plan"]["capacity_sp"], 32)
        self.assertEqual(sum(issue["story_points"] for issue in data["plan"]["issues"]), data["plan"]["selected_sp"])
        self.assertLessEqual(data["plan"]["selected_sp"], data["plan"]["capacity_sp"])


if __name__ == "__main__":
    unittest.main()
