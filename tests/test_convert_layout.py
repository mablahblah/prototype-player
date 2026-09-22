"""Where convert.py puts the pages it generates, and how the index reaches them.

Generated Principle pages live in out/prince-protos/, which is gitignored
because the converter rebuilds them. out/index.html sits one level above, so
every link it writes has to reach down into that folder.

Run with:  python3 -m unittest discover -s tests -v
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Smallest prototype in the archive, so the test stays quick.
SOURCE = REPO / "protos" / "2016.05 - journey.prd"

import convert  # noqa: E402  (needs REPO on the path first)


class ConvertOutputLayout(unittest.TestCase):
    """convert.py reads and writes relative to the working directory."""

    def setUp(self):
        self._origin = os.getcwd()
        self._sandbox = tempfile.TemporaryDirectory()
        os.chdir(self._sandbox.name)

    def tearDown(self):
        os.chdir(self._origin)
        self._sandbox.cleanup()

    def test_generated_page_lands_in_prince_protos(self):
        dest = convert.convert(SOURCE)

        self.assertEqual(Path("out/prince-protos"), Path(dest).parent)

    def test_index_links_reach_into_prince_protos(self):
        convert.convert(SOURCE)
        convert.write_index()

        index = Path("out/index.html").read_text()

        self.assertIn('href="prince-protos/', index)

    def test_converted_page_links_back_up_to_the_index(self):
        dest = convert.convert(SOURCE)

        page = Path(dest).read_text()

        self.assertIn('href="../index.html"', page)

    def test_the_index_lists_hand_made_pages_alongside_converted_ones(self):
        hand_made = Path("out/html-conversions")
        hand_made.mkdir(parents=True)
        (hand_made / "demo-page.html").write_text(
            '<title>Demo Page</title>\n'
            '<meta name="prototype-note" content="ProtoPie rebuild">\n')

        convert.convert(SOURCE)
        listed = convert.write_index()

        index = Path("out/index.html").read_text()

        self.assertEqual(2, listed)
        self.assertIn('href="html-conversions/demo-page.html"', index)
        self.assertIn("Demo Page", index)
        self.assertIn("ProtoPie rebuild", index)


if __name__ == "__main__":
    unittest.main()
