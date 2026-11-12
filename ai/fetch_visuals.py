"""
AI Shorts Factory — Visual Fetcher (Phase 3, Wikimedia Commons)
- Uses Wikimedia Commons API (no key, reliable)
- Searches multiple queries, downloads portrait-friendly images
- Saves attribution (creator + license) alongside images
"""

import re
import sys
import time
import requests
from pathlib import Path
from urllib.parse import quote

# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------- CONFIG ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISUALS_DIR = PROJECT_ROOT / "assets" / "visuals"
VISUALS_DIR.mkdir(parents=True, exist_ok=True)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
NUM_IMAGES = 4
USER_AGENT = "AI-Shorts-Factory/1.0 (educational project; contact: local)"


# ---------- HELPERS ----------
def extract_topic(text: str) -> str:
    m = re.search(r"TOPIC:\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else "abstract technology"


def build_queries(topic: str) -> list:
    stop = {"the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "with",
            "finding", "people", "how", "why"}
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", topic) if w.lower() not in stop]
    if not words:
        return ["technology"]
    qs = []
    if len(words) >= 2:
        qs.append(" ".join(words[:2]))
    qs.append(words[0])
    if len(words) >= 3:
        qs.append(words[2])
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:3]


def search_commons(query: str, limit: int = 8) -> list:
    """Search Wikimedia Commons for images. Returns list of image info dicts."""
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrnamespace": "6",          # File namespace
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|size|extmetadata",
        "iiurlwidth": "1200",         # ask for a 1200px-wide thumbnail
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(COMMONS_API, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            if not info.get("url"):
                continue
            results.append({
                "title": page.get("title", ""),
                "url": info.get("url"),
                "thumburl": info.get("thumburl") or info.get("url"),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "meta": info.get("extmetadata", {}),
            })
        return results
    except Exception as e:
        print(f"   ⚠ query '{query}' failed: {e}")
        return []


def download(url: str, out_path: Path):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=60, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)


def attribution_line(item: dict) -> str:
    meta = item.get("meta", {})
    def get(key):
        v = meta.get(key, {})
        return v.get("value", "") if isinstance(v, dict) else ""
    return (
        f"{item.get('url','')}\n"
        f"  title:   {item.get('title','(untitled)')}\n"
        f"  creator: {get('Artist') or 'unknown'}\n"
        f"  license: {get('LicenseShortName') or 'see Commons'}\n"
        f"  source:  Wikimedia Commons\n"
    )


# ---------- MAIN ----------
def main():
    if len(sys.argv) < 2:
        print('Usage: python ai\\fetch_visuals.py "<script-file>"')
        sys.exit(1)

    src = Path(sys.argv[1])
    if not src.exists():
        print(f"✗ File not found: {src}")
        sys.exit(1)

    topic = extract_topic(src.read_text(encoding="utf-8"))
    queries = build_queries(topic)
    print(f"🎬 Topic: {topic}")
    print(f"🔎 Queries: {queries}  (source=Wikimedia Commons)")

    seen_urls, picked = set(), []
    for idx, q in enumerate(queries):
        if idx > 0:
            time.sleep(1)  # be polite to Wikimedia
        print(f"   searching '{q}' ...", end=" ", flush=True)
        results = search_commons(q)
        print(f"{len(results)} hits")
        for item in results:
            url = item.get("thumburl") or item.get("url")
            if not url or url in seen_urls:
                continue
            # Prefer portrait-ish or large images; skip tiny ones
            w, h = item.get("width", 0), item.get("height", 0)
            if w < 400 or h < 400:
                continue
            seen_urls.add(url)
            picked.append(item)
            if len(picked) >= NUM_IMAGES:
                break
        if len(picked) >= NUM_IMAGES:
            break

    if not picked:
        print("✗ No images found even with broad queries.")
        sys.exit(1)

    stem = src.stem
    attribution_lines = [f"Topic: {topic}\nQueries: {queries}\nSource: Wikimedia Commons\n"]
    print(f"\n⬇  Downloading {len(picked)} images ...")
    for i, item in enumerate(picked, 1):
        url = item.get("thumburl") or item.get("url")
        out = VISUALS_DIR / f"{stem}_{i:02d}.jpg"
        try:
            download(url, out)
            print(f"   [{i}/{len(picked)}] {out.name}  ({out.stat().st_size//1024} KB)")
            attribution_lines.append(attribution_line(item))
        except Exception as e:
            print(f"   [{i}/{len(picked)}] FAILED: {e}")

    attrib_path = VISUALS_DIR / f"{stem}_attribution.txt"
    attrib_path.write_text("\n".join(attribution_lines), encoding="utf-8")
    print(f"\n📝 Attribution saved: {attrib_path.name}")
    print(f"✅ Done. Images in: {VISUALS_DIR}")


if __name__ == "__main__":
    main()