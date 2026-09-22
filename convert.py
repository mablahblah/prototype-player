#!/usr/bin/env python3
"""Convert a Principle (.prd) prototype into a standalone web page.

    python3 convert.py "protos/2019.09 - Levels Test 2.prd"
    python3 convert.py protos/*.prd

Each run also rebuilds out/index.html, the list the players link back to.
"""
import json
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


def write_index():
    """Rebuild the index from every prototype converted so far."""
    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    # Drop anything whose page has since been deleted.
    entries = {k: v for k, v in entries.items() if (PRINCE_PROTOS / k).exists()}
    listing = sorted(entries.values(), key=lambda e: e["name"])
    (OUT / "index.html").write_text(render_index(listing))
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
