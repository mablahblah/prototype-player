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
# Records what has been converted, so converting one file still lists them all.
MANIFEST = OUT / ".index.json"


def write_index():
    """Rebuild the index from every prototype converted so far."""
    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    # Drop anything whose page has since been deleted.
    entries = {k: v for k, v in entries.items() if (OUT / k).exists()}
    listing = sorted(entries.values(), key=lambda e: e["name"])
    (OUT / "index.html").write_text(render_index(listing))
    MANIFEST.write_text(json.dumps(entries, indent=2))
    return len(listing)


def convert(src):
    src = Path(src)
    model = build(load(src))
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / (src.stem + ".html")
    dest.write_text(render(model, src.stem))

    entries = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    entries[dest.name] = {
        "file": dest.name,
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
