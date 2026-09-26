"""Every hand-made page offers a copy embed control, pointing at the live address.

The pages in out/html-conversions/ are written by hand and committed, because
nothing regenerates them. They are what prototypes.mablahblah.com serves, and
what the portfolio embeds.

Two properties here cannot be observed without a browser, because they live in
JavaScript rather than in markup: the snippet the control copies, and the check
that hides the page furniture when the page is itself embedded. Those are read
out of the page's script and asserted on meaning — the snippet is parsed as
HTML and inspected, and the frame check is asserted to consult the top window
however it is spelled. The rest is read through an element tree.

Run with:  python3 -m unittest discover -s tests -v
"""
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from html_probe import parse  # noqa: E402

SITE_ROOT = REPO / "out"
PAGES = sorted((SITE_ROOT / "html-conversions").rglob("*.html"))

LIVE = "https://prototypes.mablahblah.com"


def live_address(page):
    """Where the live site serves this page: clean URLs drop .html, and a
    folder's index.html is served at the folder's own address."""
    path = page.relative_to(SITE_ROOT).with_suffix("").as_posix()
    if path.endswith("/index"):
        path = path[: -len("/index")]
    return f"{LIVE}/{path}"

SCRIPTS = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
SNIPPET = re.compile(r"'(<iframe\b[^']*)'", re.IGNORECASE)


def script_text(page):
    """Everything inside the page's script tags, joined."""
    return "\n".join(SCRIPTS.findall(page.read_text()))


def copied_snippet(page):
    """The embed snippet the control puts on the clipboard, as an element."""
    match = SNIPPET.search(script_text(page))
    if not match:
        return None
    return parse(match.group(1)).find("iframe")


class CopyEmbedControl(unittest.TestCase):

    def test_there_are_pages_to_check(self):
        self.assertNotEqual([], PAGES)

    def test_every_page_offers_a_control_named_for_copying_the_embed(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                doc = parse(page.read_text())
                named = [b.accessible_name() for b in doc.find_all("button")]
                wanted = [n for n in named
                          if "copy" in n.lower() and "embed" in n.lower()]

                self.assertEqual(1, len(wanted),
                                 f"expected one copy embed control, got {named}")

    def test_the_snippet_is_an_iframe_pointing_at_this_page_live(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                iframe = copied_snippet(page)

                self.assertIsNotNone(iframe, "no embed snippet in the script")
                self.assertEqual(live_address(page), iframe.attrs.get("src"))

    def test_the_snippet_is_sized_and_titled_for_whoever_embeds_it(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                iframe = copied_snippet(page)

                self.assertTrue(iframe.attrs.get("width"), "no width")
                self.assertTrue(iframe.attrs.get("height"), "no height")
                self.assertTrue(iframe.attrs.get("title"), "no title")

    def test_the_page_checks_whether_it_is_itself_embedded(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                script = script_text(page)

                # However it is written, deciding this means consulting the
                # window above. Cannot be exercised without a browser.
                self.assertTrue(
                    "window.top" in script or "window.parent" in script,
                    "the page never checks the window above it")


if __name__ == "__main__":
    unittest.main()
