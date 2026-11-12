"""
AI Shorts Factory — Caption Burner (Phase 4.5)
Uses FFmpeg's subtitles filter (SRT) instead of manual drawtext chains.
Avoids all Windows/FFmpeg escaping problems with commas and quotes.

Usage:
    python ai\\add_captions.py <stem>
"""

import re
import subprocess
import sys
from pathlib import Path

# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- CONFIG ----------
FFMPEG = "ffmpeg"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "output" / "scripts"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"
TEMP_DIR = PROJECT_ROOT / "output" / "temp"

# Caption style
FONT_SIZE = 20
FONT_NAME = "Arial"
PRIMARY_COLOR = "&H00FFFFFF"   # white (BGR format in SRT)
OUTLINE_COLOR = "&H00000000"   # black outline
BACK_COLOR = "&H00000000"      # black box
BOLD = 1
OUTLINE = 2
SHADOW = 1
ALIGNMENT = 2                   # bottom-center

WORDS_PER_CHUNK = 5


def extract_script(text: str) -> str:
    m = re.search(r"SCRIPT:\s*(.+)$", text, re.DOTALL)
    if not m:
        raise ValueError("No SCRIPT: section found")
    return m.group(1).strip()


def chunk_words(text: str, size: int = WORDS_PER_CHUNK) -> list:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def get_duration(video: Path) -> float:
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(video)
        ], text=True)
        return float(out.strip())
    except Exception:
        raise SystemExit("✗ Could not read video duration")


def write_srt(chunks: list, duration: float, out_path: Path):
    """Write a simple SRT with equal time slices per chunk."""
    per = duration / len(chunks)
    lines = []
    for i, chunk in enumerate(chunks):
        start = i * per
        end = (i + 1) * per
        def ts(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec - int(sec)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        lines.append(str(i + 1))
        lines.append(f"{ts(start)} --> {ts(end)}")
        lines.append(chunk)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ai\\add_captions.py <stem>")
        sys.exit(1)
    stem = sys.argv[1]

    script_path = SCRIPTS_DIR / f"{stem}.txt"
    video_path = VIDEOS_DIR / f"{stem}.mp4"
    out_path = VIDEOS_DIR / f"{stem}_captioned.mp4"
    srt_path = TEMP_DIR / f"{stem}.srt"

    if not script_path.exists():
        raise SystemExit(f"✗ Script not found: {script_path}")
    if not video_path.exists():
        raise SystemExit(f"✗ Video not found: {video_path}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    script = extract_script(script_path.read_text(encoding="utf-8"))
    duration = get_duration(video_path)
    chunks = chunk_words(script)

    print(f"🎬 Video: {video_path.name}  ({duration:.2f}s)")
    print(f"📝 Chunks: {len(chunks)} × ~{duration/len(chunks):.2f}s each")

    # Write SRT
    write_srt(chunks, duration, srt_path)
    print(f"📄 SRT written: {srt_path.name}")

    # Burn subtitles using FFmpeg's subtitles filter
    # On Windows, the SRT path needs forward slashes and escaped colon
    srt_arg = str(srt_path).replace("\\", "/").replace(":", "\\:")

    subtitle_filter = (
        f"subtitles='{srt_arg}'"
        f":force_style='FontName={FONT_NAME},FontSize={FONT_SIZE},"
        f"PrimaryColour={PRIMARY_COLOR},OutlineColour={OUTLINE_COLOR},"
        f"BackColour={BACK_COLOR},Bold={BOLD},Outline={OUTLINE},"
        f"Shadow={SHADOW},Alignment={ALIGNMENT}'"
    )

    cmd = [
        FFMPEG, "-y",
        "-i", str(video_path),
        "-vf", subtitle_filter,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(out_path),
    ]

    print("🔥 Burning captions ...", end=" ", flush=True)
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("failed\n")
        for line in result.stderr.splitlines()[-20:]:
            print(line)
        raise SystemExit(f"✗ FFmpeg exit code {result.returncode}")
    print("ok")

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Captioned video: {out_path}")
    print(f"   Size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()