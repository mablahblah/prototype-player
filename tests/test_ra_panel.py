"""Hand-made pages carry the same page furniture the converted ones do.

A converted Principle page shows a panel beside the phone: a link back to the
list, the prototype's name, and a line saying what it is. The hand-made pages
in out/html-conversions/ need the same, plus the copy embed control.

These tests read the pages as a browser would, through an element tree, and ask
for things by what they say and where they sit. Rewriting the markup to do the
same job under different ids or class names does not break them.

Run with:  python3 -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from html_probe import lowest_common_ancestor, parse  # noqa: E402

PAGES = sorted((REPO / "out" / "html-conversions").glob("*.html"))


def page_parts(page):
    """The furniture of one page: its title, back link, heading and panel."""
    doc = parse(page.read_text())
    title = doc.find("title")
    back = next((a for a in doc.find_all("a")
                 if "all prototypes" in a.text().lower()), None)
    heading = doc.find("h1")
    panel = lowest_common_ancestor(back, heading) if back and heading else None
    copy = next((b for b in doc.find_all("button")
                 if "copy" in b.accessible_name().lower()), None)
    return doc, title, back, heading, panel, copy


class HandMadePagePanel(unittest.TestCase):

    def test_there_are_pages_to_check(self):
        self.assertNotEqual([], PAGES)

    def test_every_page_offers_a_way_back_to_the_list(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                _, _, back, _, _, _ = page_parts(page)

                self.assertIsNotNone(back, "no link back to the list")
                # The list sits one folder above these pages.
                self.assertEqual("../index.html", back.attrs.get("href"))

    def test_every_page_shows_its_own_name_as_the_heading(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                _, title, _, heading, _, _ = page_parts(page)

                self.assertIsNotNone(heading, "no heading on the page")
                self.assertEqual(title.text(), heading.text())

    def test_every_page_says_what_it_is_exactly_once(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                _, _, _, _, panel, _ = page_parts(page)

                self.assertIsNotNone(panel, "no panel holding the furniture")
                described = [p.text() for p in panel.find_all("p") if p.text()]

                self.assertEqual(1, len(described),
                                 f"expected one description, got {described}")

    def test_the_copy_control_sits_with_the_rest_of_the_furniture(self):
        for page in PAGES:
            with self.subTest(page=page.name):
                _, _, _, heading, panel, copy = page_parts(page)

                self.assertIsNotNone(copy, "no copy embed control")
                # Same block as the heading, rather than loose on the page.
                self.assertIs(panel, lowest_common_ancestor(copy, heading))


if __name__ == "__main__":
    unittest.main()
