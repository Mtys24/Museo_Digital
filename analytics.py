import json
import os
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("analytics_data.json")


def _load():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"conversations": []}


def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_conversation(figure_name, question, response, response_time_ms):
    data = _load()
    data["conversations"].append({
        "timestamp": datetime.now().isoformat(),
        "figure": figure_name,
        "question": question,
        "response_length": len(response),
        "response_time_ms": round(response_time_ms),
        "question_word_count": len(question.split()),
    })
    _save(data)


def get_all_data():
    return _load()


def get_figure_stats(figure_name):
    data = _load()
    convs = [c for c in data["conversations"] if c["figure"] == figure_name]
    if not convs:
        return {
            "total": 0,
            "avg_response_time": 0,
            "avg_question_length": 0,
            "avg_response_length": 0,
            "questions": [],
            "by_hour": {},
            "by_date": {},
        }

    total = len(convs)
    avg_rt = sum(c["response_time_ms"] for c in convs) / total
    avg_ql = sum(c["question_word_count"] for c in convs) / total
    avg_rl = sum(c["response_length"] for c in convs) / total

    questions = [c["question"] for c in convs]

    by_hour = {}
    by_date = {}
    for c in convs:
        dt = datetime.fromisoformat(c["timestamp"])
        hour = dt.strftime("%H:00")
        date = dt.strftime("%Y-%m-%d")
        by_hour[hour] = by_hour.get(hour, 0) + 1
        by_date[date] = by_date.get(date, 0) + 1

    return {
        "total": total,
        "avg_response_time": round(avg_rt),
        "avg_question_length": round(avg_ql, 1),
        "avg_response_length": round(avg_rl),
        "questions": questions,
        "by_hour": by_hour,
        "by_date": by_date,
    }


def get_global_stats():
    data = _load()
    convs = data["conversations"]
    if not convs:
        return {
            "total_conversations": 0,
            "figures_used": {},
            "most_active": None,
            "today_count": 0,
        }

    figures = {}
    for c in convs:
        figures[c["figure"]] = figures.get(c["figure"], 0) + 1

    most_active = max(figures, key=figures.get) if figures else None

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = sum(1 for c in convs if c["timestamp"].startswith(today))

    return {
        "total_conversations": len(convs),
        "figures_used": figures,
        "most_active": most_active,
        "today_count": today_count,
    }
