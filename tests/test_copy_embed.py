"""Every hand-made page offers a copy embed control pointing at the live address.

The pages in out/html-conversions/ are written by hand and committed, because
nothing regenerates them. They are what prototypes.mablahblah.com serves, and
what the portfolio embeds.

Run with:  python3 -m unittest discover -s tests -v
"""
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES = sorted((REPO / "out" / "html-conversions").glob("*.html"))

LIVE = "https://prototypes.mablahblah.com"


class CopyEmbedControl(unittest.TestCase):

    def test_there_are_pages_to_check(self):
        self.assertNotEqual([], PAGES)

    def test_every_page_offers_a_copy_embed_button(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertIn('id="copy-embed"', page.read_text())

    def test_the_snippet_points_at_the_live_address(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                # Vercel serves these with clean URLs, so no .html on the end.
                self.assertIn(f"{LIVE}/{page.stem}", page.read_text())

    def test_the_button_hides_when_the_page_is_itself_embedded(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                self.assertIn("window.self !== window.top", page.read_text())


if __name__ == "__main__":
    unittest.main()
