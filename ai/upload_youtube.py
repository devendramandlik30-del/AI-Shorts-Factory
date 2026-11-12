"""
AI Shorts Factory — YouTube Uploader (Phase 5)
Uploads a finished MP4 to your YouTube channel as UNLISTED (safe test).

First run: opens browser for OAuth consent. Saves token.json for reuse.
Reads title/description from the matching script file.

Usage:
    python ai\\upload_youtube.py <stem> [--public]
"""

import re
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- CONFIG ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
CLIENT_SECRET = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

SCRIPTS_DIR = PROJECT_ROOT / "output" / "scripts"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


# ---------- HELPERS ----------
def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def find_script(stem: str) -> Path:
    p = SCRIPTS_DIR / f"{stem}.txt"
    if not p.exists():
        print(f"   ⚠ Script not found ({p}), using filename as title")
    return p


def read_metadata(stem: str) -> dict:
    """Parse TITLE / HOOK / SCRIPT from the saved script file."""
    path = find_script(stem)
    meta = {
        "title": stem.replace("_", " ")[:100],
        "description": "",
        "tags": ["shorts", "ai", "technology"],
    }
    if not path.exists():
        return meta

    text = path.read_text(encoding="utf-8")

    t = re.search(r"^TITLE:\s*(.+)$", text, re.MULTILINE)
    if t:
        meta["title"] = t.group(1).strip()[:100]

    s = re.search(r"^SCRIPT:\s*(.+)$", text, re.DOTALL | re.MULTILINE)
    if s:
        script_body = s.group(1).strip()
        meta["description"] = (
            f"{script_body}\n\n"
            f"#Shorts #AI #Technology #RescueRobots"
        )

    top = re.search(r"^TOPIC:\s*(.+)$", text, re.MULTILINE)
    if top:
        topic_words = re.findall(r"[A-Za-z]{4,}", top.group(1))
        extra = [w.lower() for w in topic_words[:3] if w.lower() not in meta["tags"]]
        meta["tags"].extend(extra)

    return meta


def upload(video: Path, meta: dict, privacy: str):
    print("🔐 Authenticating with Google ...")
    yt = get_authenticated_service()

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": "28",   # 28 = Science & Technology
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype="video/mp4")
    print(f"⬆  Uploading: {video.name}")
    print(f"   Title: {meta['title']}")
    print(f"   Privacy: {privacy}")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   ... {int(status.progress() * 100)}%", end="\r")
    print("   ... 100%")

    vid = response["id"]
    print("\n✅ Uploaded!")
    print(f"   Video ID: {vid}")
    print(f"   URL:      https://youtu.be/{vid}")
    if privacy == "unlisted":
        print("   ⚠ Status: UNLISTED — only people with link can view.")
        print("   → Review it in YouTube Studio, then make it Public when happy.")


# ---------- MAIN ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python ai\\upload_youtube.py <stem> [--public]")
        sys.exit(1)

    stem = sys.argv[1]
    privacy = "public" if "--public" in sys.argv else "unlisted"

        
    captioned = VIDEOS_DIR / f"{stem}_captioned.mp4"
    plain = VIDEOS_DIR / f"{stem}.mp4"
    if captioned.exists():
        video = captioned
        print(f"   (using captioned version)")
    elif plain.exists():
        video = plain
    else:
        print(f"✗ Video not found: {plain} (or _captioned)")
        sys.exit(1)

    meta = read_metadata(stem)
    size_mb = video.stat().st_size / (1024 * 1024)
    print(f"📁 Video: {video.name}  ({size_mb:.2f} MB)")
    upload(video, meta, privacy)


if __name__ == "__main__":
    main()