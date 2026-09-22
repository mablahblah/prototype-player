"""Hand-made pages carry the same side panel the converted ones do.

A converted Principle page shows a panel beside the phone: a link back to the
list, the prototype's name, and a line saying what it is. The hand-made pages
in out/html-conversions/ need the same, plus the copy embed button.

The whole panel disappears when the page is running inside someone else's
iframe, so an embed shows the prototype and nothing else.

Run with:  python3 -m unittest discover -s tests -v
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = sorted((REPO / "out" / "html-conversions").glob("*.html"))


class HandMadePagePanel(unittest.TestCase):

    def test_there_are_pages_to_check(self):
        self.assertNotEqual([], PAGES)

    def test_every_page_has_a_panel(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertIn('<div id="panel">', page.read_text())

    def test_the_back_link_reaches_the_list_page(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                # The list sits at out/index.html, one folder above these pages.
                self.assertIn('id="back" href="../index.html"', page.read_text())

    def test_the_panel_shows_the_page_title(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = page.read_text()
                title = re.search(r"<title>(.*?)</title>", text).group(1)
                self.assertIn(f"<h1>{title}</h1>", text)

    def test_the_panel_shows_a_description(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertRegex(page.read_text(), r'<p class="desc">\S[^<]*</p>')

    def test_the_copy_embed_button_sits_in_the_panel(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                text = page.read_text()
                panel = re.search(r'<div id="panel">(.*?)\n</div>', text, re.DOTALL)
                self.assertIsNotNone(panel, "no panel on the page")
                self.assertIn('id="copy-embed"', panel.group(1))

    def test_the_old_floating_caption_is_gone(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertNotIn('<div class="caption">', page.read_text())


if __name__ == "__main__":
    unittest.main()
