"""
AI Shorts Factory — One-Command Pipeline
Chains: script -> voice -> visuals -> video -> (optional) upload

Usage:
    python run_all.py "Your topic here"
    python run_all.py "Your topic here" --upload
    python run_all.py "Your topic here" --upload --public
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
PY = sys.executable          # the venv's python
SCRIPTS_DIR = PROJECT_ROOT / "output" / "scripts"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"


def run(step: str, cmd: list) -> bool:
    """Run a subprocess, return True on success."""
    print(f"\n{'='*60}\n▶ {step}\n{'='*60}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print(f"\n✗ Step failed: {step}")
        return False
    return True


def latest_script() -> Path:
    files = sorted(SCRIPTS_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise SystemExit("✗ No scripts found")
    return files[0]


def main():
    if len(sys.argv) < 2:
        print('Usage: python run_all.py "Your topic here" [--upload] [--public] [--no-captions]')
        sys.exit(1)

    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    topic_words = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not topic_words:
        print("✗ No topic provided")
        sys.exit(1)
    topic = " ".join(topic_words).strip()

    do_upload = "--upload" in flags
    do_captions = "--no-captions" not in flags
    privacy_flag = "--public" if "--public" in flags else None

    start = datetime.now()
    print(f"\n🎬 AI Shorts Factory — Full Pipeline")
    print(f"   Topic:    {topic}")
    print(f"   Captions: {'yes' if do_captions else 'no'}")
    print(f"   Upload:   {'yes' if do_upload else 'no'}")
    print(f"   Started:  {start.strftime('%H:%M:%S')}")

    # --- Step 1: script ---
    if not run("Step 1/5 — Generating script (Qwen 7B)",
               [PY, "main.py", topic]):
        sys.exit(1)

    script = latest_script()
    stem = script.stem
    print(f"\n💡 New script: {script.name}")

    # --- Step 2: voice ---
    if not run("Step 2/5 — Generating voiceover (edge-tts)",
               [PY, "ai/generate_voice.py", str(script)]):
        sys.exit(1)

    # --- Step 3: visuals ---
    if not run("Step 3/5 — Fetching images (Wikimedia Commons)",
               [PY, "ai/fetch_visuals.py", str(script)]):
        sys.exit(1)

    # --- Step 4: video ---
    if not run("Step 4/5 — Assembling video (FFmpeg)",
               [PY, "ai/make_video.py", stem]):
        sys.exit(1)

    video = VIDEOS_DIR / f"{stem}.mp4"
    if not video.exists():
        print(f"\n✗ Expected video not found: {video}")
        sys.exit(1)

    # --- Step 4.5: captions ---
    final_video = video
    if do_captions:
        if not run("Step 4.5/5 — Burning captions",
                   [PY, "ai/add_captions.py", stem]):
            print("   ⚠ Captions failed — falling back to plain video")
        else:
            captioned = VIDEOS_DIR / f"{stem}_captioned.mp4"
            if captioned.exists():
                final_video = captioned

    # --- Step 5: upload ---
    if do_upload:
        upload_cmd = [PY, "ai/upload_youtube.py", stem]
        if privacy_flag:
            upload_cmd.append(privacy_flag)
        if not run("Step 5/5 — Uploading to YouTube", upload_cmd):
            sys.exit(1)
    else:
        print(f"\n⏭  Skipping upload (add --upload to publish)")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*60}")
    print(f"✅ DONE in {elapsed:.1f}s")
    print(f"   Final video: {final_video}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()