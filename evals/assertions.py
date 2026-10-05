"""PromptfooのPython assertion。固定した期待値と実アプリの出力を比較する。"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backlog import BACKLOG


def result(errors, success):
    return {"pass": not errors, "score": 0 if errors else 1, "reason": " / ".join(errors) if errors else success}


def plan_matches(output, context):
    actual = json.loads(output)
    expected = context["vars"]["expected"]
    plan = actual.get("plan")
    if not plan:
        return result(["draft_sprintの結果がありません"], "")

    errors = []
    issues = plan.get("issues", [])
    keys = [issue.get("key") for issue in issues]
    canonical = {issue["key"]: issue for issue in BACKLOG}
    if plan.get("capacity_sp") != expected["capacity_sp"]:
        errors.append(f"上限SP: 期待{expected['capacity_sp']}、実際{plan.get('capacity_sp')}")
    if plan.get("selected_sp") != expected["selected_sp"]:
        errors.append(f"選定SP: 期待{expected['selected_sp']}、実際{plan.get('selected_sp')}")
    if plan.get("focus") != expected["focus"]:
        errors.append(f"対象テーマ: 期待{expected['focus']!r}、実際{plan.get('focus')!r}")
    if keys != expected["keys"]:
        errors.append(f"選定キー: 期待{expected['keys']}、実際{keys}")
    if len(keys) != len(set(keys)):
        errors.append("同じタスクが重複しています")
    if any(canonical.get(issue.get("key")) != issue for issue in issues):
        errors.append("バックログにない、または内容が違うタスクがあります")
    points = sum(issue.get("story_points", 0) for issue in issues)
    if points != plan.get("selected_sp") or points > expected["capacity_sp"]:
        errors.append(f"SP合計と上限が不整合です: {points}SP")
    return result(errors, f"{len(keys)}件・{points}/{expected['capacity_sp']}SP、対象テーマと選定順が一致")


def explanation_mentions_capacity(output, context):
    actual = json.loads(output)
    plan = actual.get("plan")
    reply = actual.get("reply") or ""
    if not plan:
        return result(["計画がないため説明を評価できません"], "")
    errors = []
    if not re.search(rf"{len(plan['issues'])}\s*件", reply):
        errors.append("採用件数への言及がありません")
    if not re.search(rf"{plan['selected_sp']}\s*SP", reply, re.IGNORECASE):
        errors.append("選定SPへの言及がありません")
    if "優先" not in reply:
        errors.append("優先度に基づく理由がありません")
    if not any(word in reply for word in ("確認", "見積", "依存")):
        errors.append("チームで確認すべき点への言及がありません")
    return result(errors, "件数・SP・優先度・確認事項を説明")
