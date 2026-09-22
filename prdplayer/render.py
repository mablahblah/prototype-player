"""Writes a model out as one standalone HTML file."""
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

RUNTIME = Path(__file__).with_name("runtime.js")

# Principle files reference fonts by PostScript name; the originals are not
# available to a browser, so fall back to a comparable system stack.
FONT_STACK = ('-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", '
              "Arial, sans-serif")

PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    margin: 0; min-height: 100vh; display: flex; gap: 24px;
    align-items: center; justify-content: center; flex-wrap: wrap;
    background: #16171a; font-family: {font};
  }}
  #frame {{ flex: none; }}
  #device {{
    width: {w}px; height: {h}px; position: relative; overflow: hidden;
    border-radius: 38px; background: #fff; transform-origin: top left;
    box-shadow: 0 24px 70px rgba(0,0,0,.55);
  }}
  #stage {{ position: absolute; inset: 0; }}
  .l {{ position: absolute; transform-origin: 50% 50%; }}
  .l > img {{
    width: 100%; height: 100%; display: block;
    object-fit: fill; user-select: none; -webkit-user-drag: none;
  }}
  .l > .t {{
    position: absolute; inset: 0; display: flex;
    align-items: center; justify-content: center; white-space: pre;
  }}
  .l::-webkit-scrollbar {{ display: none; }}
  .l {{ scrollbar-width: none; }}
  #panel {{ width: 210px; color: #8b8f98; font-size: 12px; }}
  #back {{
    display: inline-block; margin-bottom: 14px; padding: 6px 11px 6px 8px;
    border-radius: 7px; background: #24262b; color: #c8ccd4;
    text-decoration: none;
  }}
  #back:hover {{ background: #2e3138; color: #fff; }}
  #panel h1 {{ font-size: 13px; color: #e6e8ec; margin: 0 0 4px; font-weight: 600; }}
  #panel p {{ margin: 0 0 14px; line-height: 1.5; }}
  #panel button {{
    display: block; width: 100%; text-align: left; margin-bottom: 4px;
    padding: 7px 10px; border: 0; border-radius: 7px; cursor: pointer;
    background: #24262b; color: #c8ccd4; font: inherit;
  }}
  #panel button:hover {{ background: #2e3138; }}
  #panel button.on {{ background: #3b6ef5; color: #fff; }}
</style>
<div id="frame"><div id="device"><div id="stage"></div></div></div>
<div id="panel">
  <a id="back" href="../index.html">&larr; All prototypes</a>
  <h1>{title}</h1>
  <p>Click through the prototype, or jump to any screen.</p>
  {buttons}
</div>
<script>window.__PROTO__ = {model};</script>
<script>{runtime}</script>
"""


INDEX = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prototypes</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    margin: 0; padding: 56px 24px; background: #16171a; color: #8b8f98;
    font-family: {font}; font-size: 13px;
  }}
  main {{ max-width: 620px; margin: 0 auto; }}
  h1 {{ color: #e6e8ec; font-size: 19px; margin: 0 0 6px; font-weight: 600; }}
  p.lede {{ margin: 0 0 30px; line-height: 1.55; }}
  a.item {{
    display: flex; align-items: baseline; gap: 12px; padding: 13px 16px;
    margin-bottom: 6px; border-radius: 9px; background: #1e2024;
    color: #c8ccd4; text-decoration: none;
  }}
  a.item:hover {{ background: #2a2d33; color: #fff; }}
  a.item .nm {{ flex: 1; }}
  a.item .meta {{ color: #6d727b; font-size: 11px; flex: none; }}
</style>
<main>
  <h1>Prototypes</h1>
  <p class="lede">Principle prototypes rebuilt as web pages. Pick one to play it.</p>
  {items}
</main>
"""


def _count(n, noun):
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def render_index(entries):
    """List every converted prototype, in name order."""
    items = "\n  ".join(
        '<a class="item" href="{href}"><span class="nm">{name}</span>'
        '<span class="meta">{screens} &middot; {layers}</span></a>'.format(
            href=quote(e["file"]), name=escape(e["name"]),
            screens=_count(e["screens"], "screen"),
            layers=_count(e["layers"], "layer"))
        for e in entries
    )
    return INDEX.format(font=FONT_STACK, items=items)


def render(model, title):
    buttons = "\n  ".join(
        '<button data-screen="{n}" onclick="__go(\'{n}\')">{n}</button>'.format(
            n=s["name"].replace("'", "\\'"))
        for s in model["screens"]
    )
    return PAGE.format(
        title=title,
        font=FONT_STACK,
        w=int(model["width"]),
        h=int(model["height"]),
        buttons=buttons,
        model=json.dumps(model, separators=(",", ":")),
        runtime=RUNTIME.read_text(),
    )
