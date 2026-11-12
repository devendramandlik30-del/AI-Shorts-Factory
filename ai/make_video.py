"""
AI Shorts Factory — Video Assembler (Phase 4)
Combines voiceover MP3 + stock images into a 1080x1920 MP4 Short.
Uses FFmpeg: center-crop, Ken Burns zoom, concat, audio mux.

Usage:
    python ai/make_video.py <stem>
where <stem> is the shared filename prefix, e.g.
    2026-11-11_113746_rescue-robots-finding-people-in-rubble
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- CONFIG ----------
FFMPEG = "ffmpeg"   # if not on PATH, use full path:
# FFMPEG = r"C:\ffmpeg-9.0.2-essentials_build\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = PROJECT_ROOT / "output" / "audio"
VISUALS_DIR = PROJECT_ROOT / "assets" / "visuals"
VIDEO_DIR = PROJECT_ROOT / "output" / "videos"
TEMP_DIR = PROJECT_ROOT / "output" / "temp"

W, H = 1080, 1920
FPS = 30
ZOOM = 1.08          # Ken Burns max zoom (1.0 = no zoom)
CRF = 20             # quality (lower = better, bigger file)
PRESET = "medium"    # x264 speed/quality tradeoff


# ---------- HELPERS ----------
def find_audio(stem: str) -> Path:
    p = AUDIO_DIR / f"{stem}.mp3"
    if not p.exists():
        raise SystemExit(f"✗ Audio not found: {p}")
    return p


def find_images(stem: str) -> list:
    imgs = sorted(VISUALS_DIR.glob(f"{stem}_*.jpg"))
    if not imgs:
        raise SystemExit(f"✗ No images found for stem: {stem}")
    return imgs


def audio_duration(mp3: Path) -> float:
    """Return duration in seconds via ffprobe (bundled with ffmpeg)."""
    ffprobe = str(Path(FFMPEG).with_name("ffprobe.exe")) if "\\" in FFMPEG or "/" in FFMPEG else "ffprobe"
    try:
        out = subprocess.check_output([
            ffprobe, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(mp3)
        ], text=True)
        return float(out.strip())
    except Exception:
        # fallback: assume 25s
        print("   ⚠ ffprobe failed, assuming 25s")
        return 25.0


def make_clip(img: Path, seconds: float, out: Path):
    """Image -> silent 1080x1920 clip with slow zoom."""
    frames = max(1, int(round(seconds * FPS)))
    vf = (
        # scale up so we can crop to 9:16 without black bars, then zoom
        f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        f"zoompan=z='min(zoom+0.0005,{ZOOM})':d={frames}:s={W}x{H}:fps={FPS},"
        f"format=yuv420p"
    )
    cmd = [
        FFMPEG, "-y", "-loop", "1", "-i", str(img),
        "-t", f"{seconds:.3f}", "-vf", vf,
        "-r", str(FPS), "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF),
        str(out)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concat_clips(clips: list, out: Path):
    list_file = TEMP_DIR / "concat.txt"
    list_file.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c", "copy", str(out)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def add_audio(video: Path, audio: Path, out: Path):
    cmd = [
        FFMPEG, "-y", "-i", str(video), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(out)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- MAIN ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python ai\\make_video.py <stem>")
        sys.exit(1)
    stem = sys.argv[1]

    audio = find_audio(stem)
    images = find_images(stem)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    dur = audio_duration(audio)
    per_img = dur / len(images)
    print(f"🎵 Audio: {audio.name}  ({dur:.2f}s)")
    print(f"🖼  Images: {len(images)}  ({per_img:.2f}s each)")

    clips = []
    for i, img in enumerate(images, 1):
        clip = TEMP_DIR / f"clip_{i:02d}.mp4"
        print(f"   [{i}/{len(images)}] {img.name} -> clip ({per_img:.2f}s) ...", end=" ", flush=True)
        make_clip(img, per_img, clip)
        print("ok")
        clips.append(clip)

    silent = TEMP_DIR / "silent_concat.mp4"
    print("🔗 Concatenating clips ...", end=" ", flush=True)
    concat_clips(clips, silent)
    print("ok")

    final = VIDEO_DIR / f"{stem}.mp4"
    print("🔊 Adding audio ...", end=" ", flush=True)
    add_audio(silent, audio, final)
    print("ok")

    # cleanup temp
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    size_mb = final.stat().st_size / (1024 * 1024)
    print(f"\n✅ Final video: {final}")
    print(f"   Size: {size_mb:.2f} MB  |  Duration: ~{dur:.1f}s  |  {W}x{H} @ {FPS}fps")


if __name__ == "__main__":
    main()