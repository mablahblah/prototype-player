"""Builds a tiny .prd file, so tests need no prototype from the archive.

A real Principle file is an Apple binary property list written by
NSKeyedArchiver: a flat `$objects` table where entries point at each other by
UID, plus a `$top` naming the root. This writes the smallest such file the
converter accepts — one prototype, one screen, no layers.

Tests about where pages land and what the index links to do not care what is
inside a prototype, and the archive in protos/ is not published with this
repository. A fixture keeps those tests runnable on any clone.
"""
import plistlib
from plistlib import UID


def write_minimal_prd(path, screen_name="Artboard 1", width=375.0, height=812.0):
    """Write a one-screen .prd to `path` and return the path."""
    objects = [
        "$null",
        # 1 — the root: a prototype holding one screen.
        {"$class": UID(4), "screens": UID(2)},
        # 2 — the screens array.
        {"$class": UID(5), "NS.objects": [UID(3)]},
        # 3 — the screen itself.
        {
            "$class": UID(6),
            "name": screen_name,
            "size.width": width,
            "size.height": height,
        },
        # 4 to 6 — the class records the unarchiver reads names from.
        {"$classname": "PRPrototype", "$classes": ["PRPrototype", "NSObject"]},
        {"$classname": "NSMutableArray",
         "$classes": ["NSMutableArray", "NSArray", "NSObject"]},
        {"$classname": "PRScreen", "$classes": ["PRScreen", "NSObject"]},
    ]

    with open(path, "wb") as fh:
        plistlib.dump({
            "$version": 100000,
            "$archiver": "NSKeyedArchiver",
            "$top": {"root": UID(1)},
            "$objects": objects,
        }, fh, fmt=plistlib.FMT_BINARY)

    return path
