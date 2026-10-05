"""ハンズオン用の架空Jiraバックログ。起動するたびに同じ100件を生成する。"""

THEMES = [
    "ログイン", "ユーザー設定", "検索", "通知", "ダッシュボード",
    "決済", "レポート", "権限管理", "モバイル表示", "運用基盤",
]
TASKS = [
    "基本画面を作成", "入力チェックを追加", "APIを実装", "エラー表示を改善",
    "操作ログを記録", "表示速度を改善", "アクセシビリティを確認",
    "利用状況を計測", "テストを整備", "ヘルプ文を追加",
]
POINTS = [1, 2, 3, 5, 8]
PRIORITIES = ["Highest", "High", "Medium", "Low"]


def make_backlog() -> list[dict]:
    issues = []
    for theme_index, theme in enumerate(THEMES):
        for task_index, task in enumerate(TASKS):
            number = theme_index * len(TASKS) + task_index + 1
            priority = PRIORITIES[(theme_index * 2 + task_index * 3) % 11 // 3]
            issues.append({
                "key": f"SPR-{number:03d}",
                "summary": f"{theme}：{task}",
                "theme": theme,
                "priority": priority,
                "story_points": POINTS[(theme_index + task_index * 2) % len(POINTS)],
                "status": "Ready",
            })
    return issues


BACKLOG = make_backlog()
