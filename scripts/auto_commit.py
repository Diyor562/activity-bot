#!/usr/bin/env python3
import datetime as dt
import json
import os
import random
import subprocess
from pathlib import Path

# ---------- НАСТРОЙКИ ----------
MIN_COMMITS = 3
MAX_COMMITS = 5
START_HOUR_UTC = 4    # 09:00 по Ташкенту (UTC+5)
END_HOUR_UTC = 18     # 23:00 по Ташкенту
SALT = os.environ.get("PLAN_SALT", "change-me")  # делает план непредсказуемым
# --------------------------------

ACTIVITY_DIR = Path("activity")
STATE_FILE = ACTIVITY_DIR / "state.json"

MESSAGES = [
    "Update activity log", "Refactor notes", "Tweak stats", "Minor update",
    "Sync daily data", "Update progress", "Add small changes", "Improve logs",
    "Update metrics", "Routine maintenance", "Cleanup", "Save progress",
]
WORDS = ["alpha", "bravo", "cedar", "delta", "ember", "flint", "grove",
         "harbor", "iris", "juniper", "kepler", "lumen", "maple", "nova"]


def run(*args):
    subprocess.run(args, check=True)


def build_plan(today: str):
    """Детерминированный план дня: кол-во коммитов и минуты суток (UTC)."""
    rng = random.Random(f"{SALT}-{today}")
    count = rng.randint(MIN_COMMITS, MAX_COMMITS)
    pool = range(START_HOUR_UTC * 60, END_HOUR_UTC * 60)
    slots = sorted(rng.sample(pool, count))
    return slots


def load_state(today: str):
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            if state.get("date") == today:
                return state
        except json.JSONDecodeError:
            pass
    return {"date": today, "done": 0}


def make_real_change(now: dt.datetime, state: dict):
    """Реально меняет файлы: лог за месяц + json со статистикой."""
    ACTIVITY_DIR.mkdir(exist_ok=True)

    log = ACTIVITY_DIR / f"{now:%Y-%m}.md"
    if not log.exists():
        log.write_text(f"# Activity log {now:%Y-%m}\n\n")
    entry = (
        f"- {now:%Y-%m-%d %H:%M:%S} UTC | "
        f"{random.choice(WORDS)}-{random.randint(1000, 9999)} | "
        f"value={random.randint(1, 10**6)}\n"
    )
    with log.open("a") as f:
        f.write(entry)

    stats = ACTIVITY_DIR / "stats.json"
    data = {"total_updates": 0}
    if stats.exists():
        try:
            data = json.loads(stats.read_text())
        except json.JSONDecodeError:
            pass
    data["total_updates"] = data.get("total_updates", 0) + 1
    data["last_update"] = now.isoformat()
    data["random_seed"] = random.randint(0, 10**9)
    stats.write_text(json.dumps(data, indent=2))


def main():
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date().isoformat()
    minute_of_day = now.hour * 60 + now.minute

    slots = build_plan(today)
    state = load_state(today)
    due = sum(1 for s in slots if s <= minute_of_day)

    print(f"План на {today} (UTC): "
          f"{[f'{s // 60:02d}:{s % 60:02d}' for s in slots]}")
    print(f"Выполнено: {state['done']}, должно быть к сейчас: {due}")

    if state["done"] >= due:
        print("Пока коммитить не нужно.")
        return

    state["done"] += 1
    make_real_change(now, state)
    STATE_FILE.write_text(json.dumps(state, indent=2))

    run("git", "add", "-A")
    run("git", "commit", "-m", random.choice(MESSAGES))
    run("git", "push")
    print("Коммит отправлен.")


if __name__ == "__main__":
    main()
