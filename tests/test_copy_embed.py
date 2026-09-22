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

PAGES = sorted((REPO / "out" / "html-conversions").glob("*.html"))

LIVE = "https://prototypes.mablahblah.com"

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
                # Vercel serves these with clean URLs, so no .html on the end.
                self.assertEqual(f"{LIVE}/{page.stem}", iframe.attrs.get("src"))

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
