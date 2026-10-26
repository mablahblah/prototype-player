"""How convert.py syncs protos/show/ and protos/hide/ with the pages in out/.

Each source folder generates into the out/ folder of the same name. Only the
shown prototypes are listed in out/index.html, which sits one level above, so
every link it writes has to reach down into out/show/. Moving a source between
the folders moves its page; deleting the source deletes its page. A source is
a .prd file or a React site (a folder with a package.json); the site's Node
build is stood in for here, since what is checked is where it lands.

These tests convert a fixture rather than a real prototype: what they check is
where files land and what the index links say, which does not depend on what a
prototype contains. The archive in protos/ is not published with this
repository, so a fixture is also what keeps them runnable on any clone.

Run with:  python3 -m unittest discover -s tests -v
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import convert  # noqa: E402  (needs REPO on the path first)
from prd_fixture import write_minimal_prd  # noqa: E402


class SyncOutputLayout(unittest.TestCase):
    """convert.py reads and writes relative to the working directory."""

    def setUp(self):
        self._origin = os.getcwd()
        self._sandbox = tempfile.TemporaryDirectory()
        os.chdir(self._sandbox.name)
        for folder in ("show", "hide"):
            Path("protos", folder).mkdir(parents=True)

    def tearDown(self):
        os.chdir(self._origin)
        self._sandbox.cleanup()

    def add(self, folder, name="Fixture Proto"):
        return write_minimal_prd(Path("protos", folder, name + ".prd"))

    def sync(self):
        with contextlib.redirect_stdout(io.StringIO()):
            convert.sync()
        return Path("out/index.html").read_text()

    def test_a_shown_prototype_is_generated_into_out_show_and_listed(self):
        self.add("show")

        index = self.sync()

        self.assertTrue(Path("out/show/Fixture Proto.html").exists())
        self.assertIn('href="show/Fixture%20Proto.html"', index)

    def test_a_hidden_prototype_is_generated_into_out_hide_but_not_listed(self):
        self.add("hide")

        index = self.sync()

        self.assertTrue(Path("out/hide/Fixture Proto.html").exists())
        self.assertNotIn("Fixture Proto", index)

    def test_moving_a_prototype_to_hide_moves_its_page_off_the_list(self):
        src = self.add("show")
        self.sync()
        src.rename(Path("protos/hide", src.name))

        index = self.sync()

        self.assertFalse(Path("out/show/Fixture Proto.html").exists())
        self.assertTrue(Path("out/hide/Fixture Proto.html").exists())
        self.assertNotIn("Fixture Proto", index)

    def test_moving_a_prototype_to_show_moves_its_page_onto_the_list(self):
        src = self.add("hide")
        self.sync()
        src.rename(Path("protos/show", src.name))

        index = self.sync()

        self.assertFalse(Path("out/hide/Fixture Proto.html").exists())
        self.assertTrue(Path("out/show/Fixture Proto.html").exists())
        self.assertIn('href="show/Fixture%20Proto.html"', index)

    def test_deleting_a_prototype_deletes_its_page(self):
        shown, hidden = self.add("show", "Shown"), self.add("hide", "Hidden")
        self.sync()
        shown.unlink()
        hidden.unlink()

        index = self.sync()

        self.assertFalse(Path("out/show/Shown.html").exists())
        self.assertFalse(Path("out/hide/Hidden.html").exists())
        self.assertNotIn("Shown", index)

    def test_a_name_in_both_folders_stops_the_sync_before_writing(self):
        self.add("show")
        self.add("hide")

        with self.assertRaises(SystemExit):
            self.sync()

        self.assertFalse(Path("out").exists())

    def test_missing_source_folders_stop_the_sync_before_deleting(self):
        self.add("show")
        self.sync()
        for folder in ("show", "hide"):
            for prd in Path("protos", folder).iterdir():
                prd.unlink()
            Path("protos", folder).rmdir()

        with self.assertRaises(SystemExit):
            self.sync()

        self.assertTrue(Path("out/show/Fixture Proto.html").exists())

    def test_a_generated_page_links_back_up_to_the_index(self):
        self.add("show")
        self.sync()

        page = Path("out/show/Fixture Proto.html").read_text()

        self.assertIn('href="../index.html"', page)

    def test_the_index_lists_hand_made_pages_alongside_shown_ones(self):
        hand_made = Path("out/html-conversions")
        hand_made.mkdir(parents=True)
        (hand_made / "demo-page.html").write_text(
            '<title>Demo Page</title>\n'
            '<meta name="prototype-note" content="ProtoPie rebuild">\n')
        self.add("show")

        index = self.sync()

        self.assertIn('href="html-conversions/demo-page.html"', index)
        self.assertIn("Demo Page", index)
        self.assertIn("ProtoPie rebuild", index)
        self.assertIn("Fixture Proto", index)

    def test_the_index_lists_hand_made_pages_kept_in_their_own_folders(self):
        folder = Path("out/html-conversions/demo-set/demo-proto")
        folder.mkdir(parents=True)
        (folder / "index.html").write_text(
            '<title>Nested Demo</title>\n'
            '<meta name="prototype-note" content="ProtoPie rebuild">\n')

        index = self.sync()

        self.assertIn('href="html-conversions/demo-set/demo-proto/index.html"', index)
        self.assertIn("Nested Demo", index)

    def add_site(self, folder, name="Fixture Site"):
        site = Path("protos", folder, name)
        site.mkdir()
        (site / "package.json").write_text("{}")
        return site

    def sync_with_fake_build(self):
        """Sync with the Node build stood in for: it writes a front page."""
        def fake_vite_build(src, dest, base):
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "index.html").write_text(f"<title>built for {base}</title>")
        with mock.patch.object(convert, "_vite_build", side_effect=fake_vite_build):
            return self.sync()

    def test_a_site_is_built_into_app_beside_its_preview(self):
        self.add_site("show")

        self.sync_with_fake_build()

        app = Path("out/show/Fixture Site/app/index.html").read_text()
        self.assertIn("built for /show/Fixture Site/app/", app)

    def test_the_preview_shows_the_built_site_in_a_window(self):
        self.add_site("show")

        self.sync_with_fake_build()

        preview = Path("out/show/Fixture Site/index.html").read_text()
        self.assertIn('<iframe id="site" src="/show/Fixture Site/app/"', preview)

    def test_the_preview_carries_the_panel_and_embed_control(self):
        self.add_site("show")

        self.sync_with_fake_build()

        preview = Path("out/show/Fixture Site/index.html").read_text()
        self.assertIn('href="/">&larr; All prototypes</a>', preview)
        self.assertIn('id="copy-embed"', preview)
        self.assertIn("window.self !== window.top", preview)
        self.assertIn(
            'src=\\"https://prototypes.mablahblah.com/show/Fixture Site\\"', preview)

    def test_the_preview_is_named_from_the_sites_summary(self):
        site = self.add_site("show")
        (site / "prototype-summary.md").write_text(
            "# Prototype Summary: Fixture Name\n\n## What It Explores\n\n"
            "How a [fixture](x.md) reads. A second sentence.\n")

        index = self.sync_with_fake_build()

        preview = Path("out/show/Fixture Site/index.html").read_text()
        self.assertIn("<h1>Fixture Name</h1>", preview)
        self.assertIn('<p class="desc">How a fixture reads.</p>', preview)
        self.assertIn("Fixture Name", index)

    def test_a_shown_site_is_built_into_out_show_and_listed(self):
        self.add_site("show")

        index = self.sync_with_fake_build()

        self.assertTrue(Path("out/show/Fixture Site/index.html").exists())
        self.assertIn('href="show/Fixture%20Site/index.html"', index)

    def test_a_hidden_site_is_built_into_out_hide_but_not_listed(self):
        self.add_site("hide")

        index = self.sync_with_fake_build()

        self.assertTrue(Path("out/hide/Fixture Site/index.html").exists())
        self.assertNotIn("Fixture Site", index)

    def test_moving_a_site_to_hide_moves_its_build_off_the_list(self):
        site = self.add_site("show")
        self.sync_with_fake_build()
        site.rename(Path("protos/hide", site.name))

        index = self.sync_with_fake_build()

        self.assertFalse(Path("out/show/Fixture Site").exists())
        self.assertTrue(Path("out/hide/Fixture Site/index.html").exists())
        self.assertNotIn("Fixture Site", index)

    def test_deleting_a_site_deletes_its_build(self):
        site = self.add_site("show")
        self.sync_with_fake_build()
        (site / "package.json").unlink()
        site.rmdir()

        self.sync_with_fake_build()

        self.assertFalse(Path("out/show/Fixture Site").exists())

    def test_a_folder_without_a_package_json_is_not_a_site(self):
        Path("protos/show/notes").mkdir()

        index = self.sync_with_fake_build()

        self.assertFalse(Path("out/show/notes").exists())
        self.assertNotIn("notes", index)

    def test_a_site_and_a_prd_with_one_name_stop_the_sync(self):
        self.add("show", "Same Name")
        self.add_site("hide", "Same Name")

        with self.assertRaises(SystemExit):
            self.sync_with_fake_build()

        self.assertFalse(Path("out").exists())

    def add_plain_site(self, folder, name="plain-site", page='<a href="/">Home</a>'):
        site = Path("protos", folder, name)
        site.mkdir()
        (site / "index.html").write_text(page)
        return site

    def test_a_plain_site_is_copied_into_app_beside_its_preview(self):
        site = self.add_plain_site("show")
        (site / "style.css").write_text("body {}")
        (site / "launch-instructions.md").write_text("notes")

        index = self.sync()

        app = Path("out/show/plain-site/app")
        self.assertTrue((app / "style.css").exists())
        self.assertFalse((app / "launch-instructions.md").exists())
        self.assertTrue(Path("out/show/plain-site/index.html").exists())
        self.assertIn('href="show/plain-site/index.html"', index)

    def test_a_plain_sites_root_addresses_point_into_its_folder(self):
        site = self.add_plain_site(
            "show", page='<a href="/">Home</a><link href="/style.css">'
                         '<a href="/missing">Gone</a>')
        (site / "style.css").write_text("body {}")

        self.sync()

        page = Path("out/show/plain-site/app/index.html").read_text()
        self.assertIn('href="/show/plain-site/app/"', page)
        self.assertIn('href="/show/plain-site/app/style.css"', page)
        self.assertIn('href="/missing"', page)

    def test_a_folder_style_name_is_listed_as_a_title(self):
        self.add_plain_site("show", "wide-over-deep")

        index = self.sync()

        self.assertIn("Wide Over Deep", index)

    def test_a_failed_build_keeps_the_last_good_one(self):
        self.add_site("show")
        self.sync_with_fake_build()

        def failing_build(src, dest, base):
            raise convert.BuildFailed("broken")
        with mock.patch.object(convert, "_vite_build", side_effect=failing_build):
            with self.assertRaises(SystemExit):
                self.sync()

        self.assertTrue(Path("out/show/Fixture Site/app/index.html").exists())
        self.assertIn("Fixture Site", Path("out/index.html").read_text())

    def test_syncing_never_touches_hand_made_pages(self):
        page = Path("out/html-conversions/demo-page.html")
        page.parent.mkdir(parents=True)
        page.write_text(
            '<title>Demo Page</title>\n'
            '<meta name="prototype-note" content="ProtoPie rebuild">\n')

        self.sync()

        self.assertTrue(page.exists())


if __name__ == "__main__":
    unittest.main()
