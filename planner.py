"""SP上限と優先度に基づく、説明可能なスプリント案の作成。"""

from backlog import BACKLOG, PRIORITIES


def capacity(members: int, availability: float, velocity: int) -> int:
    # 演習用の仮定: 1人の稼働日1日を1SPとし、直近ベロシティを上限にする。
    return min(velocity, int(members * 10 * availability))


def draft_sprint(members: int, availability: float, velocity: int, focus: str = "") -> dict:
    limit = capacity(members, availability, velocity)
    candidates = [issue for issue in BACKLOG if not focus or focus in issue["theme"] or focus in issue["summary"]]
    ranked = sorted(candidates, key=lambda issue: (PRIORITIES.index(issue["priority"]), issue["story_points"], issue["key"]))
    selected = []
    used = 0
    for issue in ranked:
        if used + issue["story_points"] <= limit:
            selected.append(issue)
            used += issue["story_points"]
    return {
        "capacity_sp": limit,
        "selected_sp": used,
        "issues": selected,
        "focus": focus,
        "candidate_count": len(candidates),
        "rule": "優先度が高い順。同じ優先度なら小さいSPを先に選び、上限を超えるタスクは除外。",
    }
