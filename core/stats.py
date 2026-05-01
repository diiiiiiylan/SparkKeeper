"""SparkKeeper core - 统计模块"""

import json
from datetime import date, timedelta
from pathlib import Path

STATS_DIR = Path(__file__).parent.parent / "configs"


def _stats_path(plugin_name):
    return STATS_DIR / f"{plugin_name}_stats.json"


def load_stats(plugin_name):
    path = _stats_path(plugin_name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"history": [], "total_sent": 0, "total_failed": 0}


def save_stats(plugin_name, stats):
    path = _stats_path(plugin_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


def record(plugin_name, success, failed):
    stats = load_stats(plugin_name)
    stats["history"].append({
        "date": date.today().isoformat(),
        "success": success,
        "failed": failed,
    })
    stats["history"] = stats["history"][-90:]
    stats["total_sent"] = stats.get("total_sent", 0) + success
    stats["total_failed"] = stats.get("total_failed", 0) + failed
    save_stats(plugin_name, stats)


def get_streak(plugin_name):
    stats = load_stats(plugin_name)
    dates = {item["date"] for item in stats["history"] if item["success"] > 0}
    streak = 0
    d = date.today()
    while d.isoformat() in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


def get_calendar(plugin_name, days=30):
    """返回最近 N 天的打卡状态列表: 'ok' / 'fail' / 'miss'"""
    stats = load_stats(plugin_name)
    ok_dates = {item["date"] for item in stats["history"] if item["success"] > 0}
    fail_dates = {item["date"] for item in stats["history"]
                  if item["success"] == 0 and item["failed"] > 0}
    today = date.today()
    result = []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in ok_dates:
            result.append("ok")
        elif d in fail_dates:
            result.append("fail")
        else:
            result.append("miss")
    return result
