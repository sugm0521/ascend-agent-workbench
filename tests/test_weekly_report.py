"""Exercise the real report renderer; use NODE_BINARY/NODE_PATH if needed."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / ".agents/skills/ascend-weekly-report/scripts/render_reports.cjs"


class RenderedHTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    @property
    def hrefs(self):
        return [attrs["href"] for tag, attrs in self.elements if tag == "a"]


class WeeklyReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which(os.environ.get("NODE_BINARY", "node"))
        if not cls.node:
            raise unittest.SkipTest("Node.js is unavailable; set NODE_BINARY to an existing executable")
        probe = subprocess.run(
            [cls.node, "-e", "const {Marked,Renderer}=require('marked'); if(!Marked||!Renderer) process.exit(1)"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        if probe.returncode:
            raise unittest.SkipTest("Existing marked package is unavailable or incompatible; set NODE_PATH")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / "work-source" / "report.md"
        self.improvements = self.root / "improvement-source" / "report.md"
        self.output = self.root / "reading-copy" / "index.html"
        for source in (self.work, self.improvements):
            source.parent.mkdir()
            source.write_text("# Report\n\nContent.\n", encoding="utf-8")

    def render(self, output=None):
        return subprocess.run(
            [self.node, str(RENDERER), "--work", str(self.work),
             "--improvements", str(self.improvements), "--output", str(output or self.output),
             "--period", "2026-10-12 through 2026-10-18"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=30,
        )

    def rendered(self):
        result = self.render()
        self.assertEqual(result.returncode, 0, result.stderr)
        return RenderedHTML(self.output.read_text(encoding="utf-8"))

    def test_each_document_resolves_evidence_from_its_own_directory(self):
        for source in (self.work, self.improvements):
            (source.parent / "evidence.txt").write_text(source.parent.name, encoding="utf-8")
            source.write_text("# Report\n\n[Evidence](evidence.txt?download=1#details)\n", encoding="utf-8")
        hrefs = self.rendered().hrefs
        for source in (self.work, self.improvements):
            expected = (source.parent / "evidence.txt").as_uri() + "?download=1#details"
            self.assertEqual(hrefs.count(expected), 1)
        self.assertNotIn((self.output.parent / "evidence.txt").as_uri(), hrefs)

    def test_fragment_links_remain_scoped_to_each_report(self):
        for source in (self.work, self.improvements):
            source.write_text("# Report\n\n## Evidence\n\n[Jump](#evidence)\n", encoding="utf-8")
        html = self.rendered()
        ids = {attrs["id"] for _, attrs in html.elements if "id" in attrs}
        for report in ("work", "improvements"):
            self.assertIn(f"#{report}-evidence", html.hrefs)
            self.assertIn(f"{report}-evidence", ids)
        self.assertNotIn("#evidence", html.hrefs)

    def test_filters_dangerous_links_raw_html_and_images(self):
        self.work.write_text(
            "# Report\n\n[Safe](https://example.test/evidence?q=1#ok)\n\n"
            "[Script](javascript:alert%281%29)\n\n[Data](data:text/html,unsafe)\n\n"
            "[External](//example.test/unsafe)\n\n[Mail](mailto:someone@example.test)\n\n"
            '<script>alert("unsafe")</script>\n\n'
            '<a href="javascript:alert(1)">Raw link</a>\n\n'
            "![Remote image](https://example.test/image.png)\n", encoding="utf-8",
        )
        html = self.rendered()
        self.assertIn("https://example.test/evidence?q=1#ok", html.hrefs)
        self.assertFalse(any(h.startswith(("javascript:", "data:", "mailto:", "//")) for h in html.hrefs))
        self.assertFalse(any(tag in ("script", "img") for tag, _ in html.elements))
        text = self.output.read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("Remote image", text)

    def test_refuses_output_that_overwrites_input(self):
        before = self.work.read_bytes()
        result = self.render(output=self.work)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Output must not overwrite", result.stderr)
        self.assertEqual(self.work.read_bytes(), before)

    def test_rejects_empty_and_oversized_inputs_without_replacing_output(self):
        self.output.parent.mkdir()
        self.output.write_text("Existing reader", encoding="utf-8")
        for source in (" \n", "a" * 1000000):
            with self.subTest(length=len(source)):
                self.work.write_text(source, encoding="utf-8")
                result = self.render()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.output.read_text(encoding="utf-8"), "Existing reader")


if __name__ == "__main__":
    unittest.main()
