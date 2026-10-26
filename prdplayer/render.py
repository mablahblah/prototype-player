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
<title>Prototype Player</title>
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
  <h1>Prototype Player</h1>
  <p class="lede">Prototypes from retired design tools, rebuilt as web pages. Pick one to play it.</p>
  {items}
</main>
"""


def _count(n, noun):
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def render_index(entries):
    """List every converted prototype, in name order."""
    def meta(e):
        # hand-made pages have no Principle file to count screens/layers from
        if "note" in e:
            return escape(e["note"])
        return "{screens} &middot; {layers}".format(
            screens=_count(e["screens"], "screen"),
            layers=_count(e["layers"], "layer"))

    items = "\n  ".join(
        '<a class="item" href="{href}"><span class="nm">{name}</span>'
        '<span class="meta">{meta}</span></a>'.format(
            href=quote(e["file"]), name=escape(e["name"]), meta=meta(e))
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


# Where the published player lives; embed snippets point here.
LIVE = "https://prototypes.mablahblah.com"

# A React site's preview: the site in a desktop window that fills the room it
# is given, with the same panel and copy embed control the hand-made pages
# carry. Embedded in someone else's page it is the site and nothing else.
SITE_PREVIEW = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="prototype-note" content="React prototype">
<script>
// An embedded preview is the site and nothing else: no window, no panel.
if (window.self !== window.top) document.documentElement.className += ' embedded';
</script>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; display: flex; flex-wrap: wrap; gap: 24px;
    align-items: center; justify-content: center; padding: 30px;
    background: #16171a; font-family: {font};
  }}

  /* the window takes every bit of width the panel leaves, so the site inside
     lays itself out as it would in a browser that size */
  #window {{
    flex: 1 1 720px; max-width: 1600px; height: calc(100vh - 60px); min-height: 480px;
    display: flex; flex-direction: column; overflow: hidden;
    border-radius: 10px; background: #fff;
    box-shadow: 0 24px 70px rgba(0,0,0,.55);
  }}
  #bar {{
    flex: none; height: 34px; display: flex; align-items: center; gap: 7px;
    padding: 0 12px; background: #24262b;
  }}
  #bar i {{ flex: none; width: 11px; height: 11px; border-radius: 50%; background: #3a3d44; }}
  #bar .addr {{
    flex: 1; height: 20px; margin: 0 60px 0 18px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    background: #1a1c20; color: #8b8f98; font-size: 11px;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
  }}
  #site {{ flex: 1; display: block; width: 100%; border: 0; background: #fff; }}

  /* embed mode: the frame holds the site and nothing else, at any size */
  html.embedded body {{ padding: 0; display: block; background: transparent; }}
  html.embedded #window {{
    height: 100vh; min-height: 0; max-width: none;
    border-radius: 0; box-shadow: none;
  }}
  html.embedded #bar, html.embedded #panel {{ display: none; }}

  #panel {{
    flex: none; width: 210px; max-width: 90vw;
    color: #8b8f98; font-size: 12px;
  }}
  /* back link and icon button share one row, pinned to opposite edges */
  #panel-top {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }}
  #back {{
    display: inline-block; padding: 6px 11px 6px 8px;
    border-radius: 7px; background: #24262b; color: #c8ccd4;
    text-decoration: none;
  }}
  #back:hover {{ background: #2e3138; color: #fff; }}
  #panel h1 {{ font-size: 13px; color: #e6e8ec; margin: 0 0 4px; font-weight: 600; }}
  #panel p {{ margin: 0; line-height: 1.5; }}
  #copy-embed {{
    display: inline-flex; align-items: center; justify-content: center;
    flex: 0 0 auto; width: 28px; height: 28px; padding: 0;
    border: 1px solid #33363d; border-radius: 7px; background: #1e2023;
    color: #b9bdc4; cursor: pointer;
    transition: background-color .15s ease, color .15s ease, border-color .15s ease;
  }}
  #copy-embed svg {{ display: block; }}
  #copy-embed:hover {{ background: #26292e; color: #e7e8ea; }}
  #copy-embed[data-ce-state="done"] {{ background: #204a3f; color: #7fd9b9; border-color: #2c5c4d; }}
  #copy-embed[data-ce-state="error"] {{ background: #4a2020; color: #e29a9a; border-color: #5c2c2c; }}
</style>

<div id="window">
  <div id="bar"><i></i><i></i><i></i><span class="addr">{title}</span></div>
  <iframe id="site" src="{app}" title="{title}"></iframe>
</div>

<div id="panel">
  <div id="panel-top">
    <a id="back" href="/">&larr; All prototypes</a>
    <button type="button" id="copy-embed" aria-label="Copy embed code" title="Copy embed code">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <polyline points="9 6 3 12 9 18"></polyline>
        <line x1="14" y1="4" x2="10" y2="20"></line>
        <polyline points="15 6 21 12 15 18"></polyline>
      </svg>
    </button>
  </div>
  <h1>{title}</h1>
  <p class="desc">{about}</p>
</div>

<script>
(function () {{
  // inside someone else's iframe, the panel has no job to do
  if (window.self !== window.top) return;

  var ceBtn = document.getElementById('copy-embed');
  var CE_SNIPPET = {snippet};

  // the button has no text label to swap, so success briefly swaps the code
  // glyph for a tick; failure is shown by colour alone (see the CSS states above)
  var CE_ICON_DEFAULT = ceBtn.innerHTML;
  var CE_ICON_CHECK = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><polyline points="20 6 9 17 4 12"></polyline></svg>';

  var ceResetTimer = null;
  function ceShowState(state) {{
    clearTimeout(ceResetTimer);
    ceBtn.dataset.ceState = state;
    ceBtn.innerHTML = state === 'done' ? CE_ICON_CHECK : CE_ICON_DEFAULT;
    ceResetTimer = setTimeout(function () {{
      delete ceBtn.dataset.ceState;
      ceBtn.innerHTML = CE_ICON_DEFAULT;
    }}, 1800);
  }}

  function ceFallbackCopy(text) {{
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.top = '-1000px';
    ta.style.left = '-1000px';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, text.length);
    var ok = false;
    try {{
      ok = document.execCommand('copy');
    }} catch (e) {{
      ok = false;
    }}
    document.body.removeChild(ta);
    return ok;
  }}

  ceBtn.addEventListener('click', function () {{
    function finish(ok) {{
      ceShowState(ok ? 'done' : 'error');
    }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(CE_SNIPPET).then(
        function () {{ finish(true); }},
        function () {{ finish(ceFallbackCopy(CE_SNIPPET)); }}
      );
    }} else {{
      finish(ceFallbackCopy(CE_SNIPPET));
    }}
  }});
}})();
</script>
"""


def render_site_preview(title, about, app, live):
    """The preview page for a React site whose build is served at `app`.

    `live` is the preview's own address on the published player, which the
    copied embed snippet points at.
    """
    snippet = ('<iframe src="{src}" width="100%" height="800" style="border:0" '
               'title="{title}" loading="lazy"></iframe>').format(
                   src=escape(live), title=escape(title))
    return SITE_PREVIEW.format(
        title=escape(title),
        about=escape(about),
        font=FONT_STACK,
        app=escape(app),
        # a JS string literal; "</" is split so it can never close the script
        snippet=json.dumps(snippet).replace("</", "<\\/"),
    )
