#!/usr/bin/env python3
"""Sync the Principle (.prd) prototypes in protos/ with the pages in out/.

    python3 convert.py

protos/show/ holds the prototypes the player lists; protos/hide/ holds the ones
it generates but leaves off the list. Each holds .prd files and web sites: a
folder with a package.json is a React site, built with its own Vite; a folder
with only an index.html is a plain site, copied as it is. Each site gets a
preview page around it. Each run converts or builds both folders into
out/show/ and out/hide/, deletes any page whose source is gone from its folder,
and rebuilds out/index.html. Moving a source between the folders moves its
page; deleting the source deletes its page.

Building a React site needs Node.js; the site's own Vite does the build.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from prdplayer.unarchive import load
from prdplayer.model import build
from prdplayer.render import LIVE, render, render_index, render_site_preview

PROTOS = Path("protos")
OUT = Path("out")
# Each source folder generates into the out/ folder of the same name.
FOLDERS = ("show", "hide")
# Pages written by hand, dropped in here directly. Nothing generates or
# deletes these; the folder itself is the record, re-scanned on every rebuild.
HAND_MADE = OUT / "html-conversions"
# The Vite config a React site is built with, so it works inside a folder.
SITE_CONFIG = Path(__file__).resolve().parent / "prdplayer" / "site.config.mjs"


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


def write_index(shown):
    """Rebuild the index from the shown prototypes plus any hand-made pages."""
    listing = list(shown) + _hand_made_entries()
    listing.sort(key=lambda e: e["name"])
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(render_index(listing))
    return len(listing)


def convert(src, folder):
    """Convert one .prd into out/<folder>/ and return its index entry."""
    src = Path(src)
    model = build(load(src))
    dest_dir = OUT / folder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (src.stem + ".html")
    dest.write_text(render(model, src.stem))

    print(f"{folder}/{src.name}: {len(model['screens'])} screens, "
          f"{len(model['nodes'])} layers, {len(model['images'])} images, "
          f"{len(model['events'])} events, {len(model['drivers'])} drivers")
    print(f"  -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    # "file" is relative to out/, which is where index.html sits.
    return {
        "file": dest.relative_to(OUT).as_posix(),
        "name": src.stem,
        "screens": len(model["screens"]),
        "layers": len(model["nodes"]),
    }


class BuildFailed(Exception):
    """A site that could not be built; its previous build is left in place."""


def _vite_build(src, dest, base):
    """Build the React site in `src` into `dest`, to be served from `base`."""
    if not (src / "node_modules").is_dir():
        subprocess.run(["npm", "install"], cwd=src, check=True)
    env = dict(os.environ, SITE=str(src.resolve()), BASE=base)
    built = subprocess.run(
        ["npx", "vite", "build", "--config", str(SITE_CONFIG),
         "--configLoader", "native", "--outDir", str(dest.resolve()),
         "--emptyOutDir"],
        cwd=src, env=env)
    if built.returncode:
        raise BuildFailed(f"{src}: Vite could not build it")


# A quoted or url() address starting at the root of the server: "/x.css".
ROOT_ADDRESS = re.compile(r"""(["'(])/([^"'()\s?#]*)""")
# A link to the root itself, which in the original opened the site again.
ROOT_LINK = re.compile(r"""\bhref=(["'])/\1""")


def _copy_plain(src, dest, base):
    """Copy a plain site into `dest`, pointing its root addresses at `base`.

    Served from its own folder, the site's root was the site itself. Here the
    root is the player, so an address that named a file of the site, or a
    link to the root, gets `base` in front. Anything else is left alone.
    """
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("*.md", "node_modules"))

    def rebase(match):
        quote, rest = match.groups()
        if rest and (src / rest).is_file():
            return quote + base + rest
        return match.group(0)

    for path in dest.rglob("*"):
        if path.suffix not in (".html", ".css", ".js") or not path.is_file():
            continue
        text = path.read_text()
        fixed = ROOT_LINK.sub(lambda m: f"href={m.group(1)}{base}{m.group(1)}", text)
        fixed = ROOT_ADDRESS.sub(rebase, fixed)
        if fixed != text:
            path.write_text(fixed)


def _title(name):
    """A folder-style name ("grey-swap") as a title ("Grey Swap")."""
    if " " in name or "-" not in name:
        return name
    return " ".join(word[:1].upper() + word[1:] for word in name.split("-"))


def _site_info(src):
    """A site's name and one-line description, from its prototype-summary.md.

    The summary opens with a "# Prototype Summary: {name}" heading, or
    "# Prototype: {name}"; the first sentence of its first paragraph says what
    the prototype is. Without the file, the folder's name stands in and there
    is no description.
    """
    name, about = src.name, ""
    summary = src / "prototype-summary.md"
    if summary.is_file():
        for line in summary.read_text().splitlines():
            line = line.strip()
            if line.startswith("# ") and name == src.name:
                name = re.sub(r"^Prototype( Summary)?:\s*", "", line[2:]).strip() or src.name
            elif line and not line.startswith(("#", "|", "-", ">", "[")):
                # markdown links keep their text, and code marks are dropped
                text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line).replace("`", "")
                about = re.split(r"(?<=\.)\s", text, maxsplit=1)[0]
                break
    return _title(name), about


def build_site(src, folder):
    """Build a site and its preview page into out/<folder>/<name>/.

    The preview is the folder's index.html; the site itself goes into app/
    beside it, which the preview shows in a desktop window. Everything is
    made in a scratch folder first, so a failed build leaves the last good
    one where it was.
    """
    src = Path(src)
    dest = OUT / folder / src.name
    base = f"/{folder}/{src.name}/"
    react = (src / "package.json").is_file()
    name, about = _site_info(src)
    entry = {
        "file": f"{folder}/{src.name}/index.html",
        "name": name,
        "note": "React prototype" if react else "Web prototype",
    }

    scratch = OUT / folder / f".{src.name}.building"
    if scratch.exists():
        shutil.rmtree(scratch)
    try:
        if react:
            _vite_build(src, scratch / "app", base + "app/")
        else:
            _copy_plain(src, scratch / "app", base + "app/")
    except BuildFailed:
        if scratch.exists():
            shutil.rmtree(scratch)
        raise
    (scratch / "index.html").write_text(render_site_preview(
        name, about, base + "app/", LIVE + base.rstrip("/")))
    if dest.exists():
        shutil.rmtree(dest)
    scratch.rename(dest)

    print(f"{folder}/{src.name}: {entry['note']}")
    print(f"  -> {dest}/")
    return entry


def _is_site(path):
    return (path / "package.json").is_file() or (path / "index.html").is_file()


def _sources(folder):
    """The .prd files and sites in protos/<folder>/."""
    root = PROTOS / folder
    if not root.is_dir():
        return [], []
    prds = sorted(root.glob("*.prd"))
    sites = sorted(p for p in root.iterdir() if p.is_dir() and _is_site(p))
    return prds, sites


def _build_or_keep(src, folder, failed):
    """Build a site; if it fails, note why and keep listing its last build."""
    try:
        return build_site(src, folder)
    except BuildFailed as reason:
        failed.append(str(reason))
        if (OUT / folder / src.name / "index.html").is_file():
            name, _ = _site_info(src)
            react = (src / "package.json").is_file()
            return {"file": f"{folder}/{src.name}/index.html", "name": name,
                    "note": "React prototype" if react else "Web prototype"}
        return None


def sync():
    """Make out/show/ and out/hide/ match protos/show/ and protos/hide/."""
    if not any((PROTOS / f).is_dir() for f in FOLDERS):
        # Without either folder every generated page would be deleted, which
        # is far more likely a missing archive than an intent.
        sys.exit("protos/show/ and protos/hide/ not found; nothing synced.")

    sources = {f: _sources(f) for f in FOLDERS}
    # A name used twice would give one prototype two pages, or two
    # prototypes one address.
    names = [p.stem for f in FOLDERS for p in sources[f][0]] + \
            [p.name for f in FOLDERS for p in sources[f][1]]
    clashes = {n for n in names if names.count(n) > 1}
    if clashes:
        sys.exit("Used by more than one prototype in protos/show/ and "
                 "protos/hide/: " + ", ".join(sorted(clashes)))

    failed = []
    entries = {}
    for f in FOLDERS:
        built = [_build_or_keep(src, f, failed) for src in sources[f][1]]
        entries[f] = ([convert(src, f) for src in sources[f][0]]
                      + [e for e in built if e])

    # A page whose source has left its folder was moved or deleted there.
    for f in FOLDERS:
        prds, sites = sources[f]
        keep_pages = {src.stem + ".html" for src in prds}
        keep_sites = {src.name for src in sites}
        if not (OUT / f).is_dir():
            continue
        for page in sorted((OUT / f).iterdir()):
            if page.is_dir() and page.name not in keep_sites:
                shutil.rmtree(page)
            elif page.suffix == ".html" and page.name not in keep_pages:
                page.unlink()
            else:
                continue
            print(f"removed {page}")

    print(f"index: out/index.html ({write_index(entries['show'])} prototypes, "
          f"{len(entries['hide'])} hidden)")
    if failed:
        sys.exit("Not rebuilt, so the last build was kept:\n  " + "\n  ".join(failed))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(__doc__)
    sync()
