"""
AI Shorts Factory — Voice Generator (Phase 2)
Converts a script text file into an MP3 using edge-tts (free Microsoft voices).
"""

import asyncio
import re
import sys
from pathlib import Path

import edge_tts

# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- CONFIG ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "output" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Voice choices (all free):
#   en-US-GuyNeural      -> deep male, dramatic
#   en-US-AriaNeural     -> female, energetic
#   en-US-ChristopherNeural -> mature male, documentary
#   en-US-JennyNeural    -> female, friendly
VOICE = "en-US-GuyNeural"
RATE = "+10%"      # slightly faster = better for Shorts
VOLUME = "+0%"


def extract_script(text: str) -> str:
    """Pull only the SCRIPT: section from a saved file."""
    m = re.search(r"SCRIPT:\s*(.+)$", text, re.DOTALL)
    if not m:
        raise ValueError("No SCRIPT: section found in file")
    return m.group(1).strip()


async def synthesize(text: str, out_path: Path, voice: str = VOICE):
    """Run edge-tts and save MP3."""
    communicate = edge_tts.Communicate(text, voice, rate=RATE, volume=VOLUME)
    await communicate.save(str(out_path))


def main():
    if len(sys.argv) < 2:
        print('Usage: python ai\\generate_voice.py "<path-to-script-file>"')
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"✗ File not found: {src}")
        sys.exit(1)

    raw = src.read_text(encoding="utf-8")
    script = extract_script(raw)
    words = len(re.findall(r"\b[\w'-]+\b", script))

    out_name = src.stem + ".mp3"
    out_path = AUDIO_DIR / out_name

    print(f"🎙  Voice: {VOICE}  |  Rate: {RATE}")
    print(f"📝 Words: {words}")
    print(f"⏳ Synthesizing ...", end=" ", flush=True)

    asyncio.run(synthesize(script, out_path))

    size_kb = out_path.stat().st_size / 1024
    print(f"done ({size_kb:.1f} KB)")
    print(f"💾 Saved: {out_path}")


if __name__ == "__main__":
    main()