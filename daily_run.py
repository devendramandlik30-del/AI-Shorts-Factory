"""
AI Shorts Factory — Daily Runner
Runs the full pipeline ONCE per day, using the next topic from topics.txt.
If today's video already exists, exits immediately (guard against double-runs).

Intended to be triggered at login by Windows Task Scheduler.

Usage:
    python daily_run.py            # normal (respects once-per-day guard)
    python daily_run.py --force    # ignore guard, run anyway
"""

import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Force UTF-8 output so emoji prints don't crash on Windows cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
PY = sys.executable

TOPICS_FILE = PROJECT_ROOT / "topics.txt"
STATE_FILE = PROJECT_ROOT / "logs" / "last_run.txt"
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def today_str() -> str:
    return date.today().isoformat()


def already_ran_today() -> bool:
    if not STATE_FILE.exists():
        return False
    return STATE_FILE.read_text(encoding="utf-8").strip() == today_str()


def mark_ran_today():
    STATE_FILE.write_text(today_str(), encoding="utf-8")


def pop_next_topic() -> str:
    """Take the first non-empty line from topics.txt and remove it."""
    if not TOPICS_FILE.exists():
        raise SystemExit(f"✗ topics.txt not found at {TOPICS_FILE}")
    lines = TOPICS_FILE.read_text(encoding="utf-8").splitlines()
    non_empty = [
        (i, l.strip())
        for i, l in enumerate(lines)
        if l.strip() and not l.strip().startswith("#")
    ]
    if not non_empty:
        raise SystemExit("✗ topics.txt is empty — add a topic per line")
    idx, topic = non_empty[0]
    remaining = lines[:idx] + lines[idx + 1:]
    TOPICS_FILE.write_text("\n".join(remaining) + "\n", encoding="utf-8")
    return topic


def main():
    force = "--force" in sys.argv

    if not force and already_ran_today():
        print(f"✓ Already ran today ({today_str()}). Use --force to override.")
        return

    topic = pop_next_topic()
    log_path = LOG_DIR / f"daily_{today_str()}.log"

    print(f"\n🎬 Daily run — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Topic: {topic}")
    print(f"   Log:   {log_path.name}\n")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"\n===== {datetime.now().isoformat()} — topic: {topic} =====\n")

        proc = subprocess.Popen(
            [PY, "run_all.py", topic, "--upload"],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        for line in proc.stdout:
            try:
                print(line, end="")
            except UnicodeEncodeError:
                print(line.encode("ascii", "replace").decode("ascii"), end="")
            logf.write(line)

        proc.wait()

        if proc.returncode == 0:
            mark_ran_today()
            print("\n✅ Daily run complete")
            logf.write("\n✅ SUCCESS\n")
        else:
            print(f"\n✗ Daily run failed (exit {proc.returncode}) — topic was '{topic}'")
            print("   Re-adding topic to end of queue so it retries tomorrow")
            with open(TOPICS_FILE, "a", encoding="utf-8") as tf:
                tf.write(topic + "\n")
            logf.write(f"\n✗ FAILED (exit {proc.returncode})\n")


if __name__ == "__main__":
    main()