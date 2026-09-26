#!/usr/bin/env python3
"""Convert a Principle (.prd) prototype into a standalone web page.

    python3 convert.py "protos/2019.09 - Levels Test 2.prd"
    python3 convert.py protos/*.prd

Each run also rebuilds out/index.html, the list the players link back to.
"""
import json
import re
import sys
from pathlib import Path

from prdplayer.unarchive import load
from prdplayer.model import build
from prdplayer.render import render, render_index

OUT = Path("out")
# Generated pages live one level below the index, so its links can reach them.
PRINCE_PROTOS = OUT / "prince-protos"
# Records what has been converted, so converting one file still lists them all.
MANIFEST = PRINCE_PROTOS / ".index.json"
# Pages written by hand, dropped in here directly. No manifest tracks these;
# the folder itself is the record, so it's re-scanned on every index rebuild.
HAND_MADE = OUT / "html-conversions"


def _prototype_note(html):
    """The content of <meta name="prototype-note" content="...">, if present."""
    for tag in re.findall(r"<meta[^>]*>", html, re.IGNORECASE):
        if re.search(r'name=["\']prototype-note["\']', tag, re.IGNORECASE):
            match = re.search(r'content=["\'](.*?)["\']', tag, re.IGNORECASE)
            if match:
                return match.group(1)
    return None


def _hand_made_entries():
    """Build index entries for every page under out/html-conversions/, found fresh each run.

    Pages may sit at any depth, since a set of related prototypes shares a folder
    and each prototype in it has a folder of its own.
    """
    if not HAND_MADE.exists():
        return []
    entries = []
    for path in sorted(HAND_MADE.rglob("*.html")):
        html = path.read_text()
        title = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        entry = {
            "file": path.relative_to(OUT).as_posix(),
            "name": title.group(1).strip() if title else path.stem,
        }
        note = _prototype_note(html)
        if note is not None:
            entry["note"] = note
        entries.append(entry)
    return entries


def write_index():
    """Rebuild the index from converted prototypes plus any hand-made pages."""
    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    # Drop anything whose page has since been deleted.
    entries = {k: v for k, v in entries.items() if (PRINCE_PROTOS / k).exists()}
    listing = list(entries.values()) + _hand_made_entries()
    listing.sort(key=lambda e: e["name"])
    (OUT / "index.html").write_text(render_index(listing))
    # Only converted entries are persisted; hand-made pages are never recorded,
    # since the folder itself is the source of truth for those.
    MANIFEST.write_text(json.dumps(entries, indent=2))
    return len(listing)


def convert(src):
    src = Path(src)
    model = build(load(src))
    PRINCE_PROTOS.mkdir(parents=True, exist_ok=True)
    dest = PRINCE_PROTOS / (src.stem + ".html")
    dest.write_text(render(model, src.stem))

    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    # Keyed by filename alone, so write_index() can check it against
    # PRINCE_PROTOS; "file" carries the path relative to out/, which is what
    # index.html (one level up) needs for its link.
    entries[dest.name] = {
        "file": f"prince-protos/{dest.name}",
        "name": src.stem,
        "screens": len(model["screens"]),
        "layers": len(model["nodes"]),
    }
    MANIFEST.write_text(json.dumps(entries, indent=2))

    print(f"{src.name}: {len(model['screens'])} screens, "
          f"{len(model['nodes'])} layers, {len(model['images'])} images, "
          f"{len(model['events'])} events, {len(model['drivers'])} drivers")
    print(f"  -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        convert(arg)
    print(f"index: out/index.html ({write_index()} prototypes)")
