import unittest
import tempfile
import shutil
import csv
from pathlib import Path

import sys
# Make it possible to import agents
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from agents import qc_agent

class TestQCCheck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_submittals = Path(self.temp_dir)

        # Monkeypatch the SUBMITTALS_DIR in qc_agent
        self.original_submittals_dir = qc_agent.SUBMITTALS_DIR
        qc_agent.SUBMITTALS_DIR = self.mock_submittals

    def tearDown(self):
        # Restore original
        qc_agent.SUBMITTALS_DIR = self.original_submittals_dir
        shutil.rmtree(self.temp_dir)

    def setup_project(self, project_name="TestProject"):
        project_dir = self.mock_submittals / project_name
        project_dir.mkdir()
        return project_dir

    def test_project_does_not_exist(self):
        report = qc_agent.qc_check("nonexistent_project")
        self.assertIn("Project directory does not exist", report["failed"])
        self.assertEqual(report["score"], 0)

    def test_missing_directories(self):
        project_name = "MissingDirs"
        project_dir = self.setup_project(project_name)
        # Create only 01-cover
        (project_dir / "01-cover").mkdir()

        report = qc_agent.qc_check(project_name)
        self.assertIn("Missing directory: 02-index/", report["failed"])
        self.assertIn("Missing directory: 03-items/", report["failed"])
        self.assertIn("Missing directory: 04-attachments/", report["failed"])
        self.assertIn("Directory exists: 01-cover/", report["passed"])

    def test_missing_manifest(self):
        project_name = "MissingManifest"
        project_dir = self.setup_project(project_name)
        report = qc_agent.qc_check(project_name)
        self.assertIn("Manifest file missing", report["failed"])

    def test_empty_manifest(self):
        project_name = "EmptyManifest"
        project_dir = self.setup_project(project_name)
        (project_dir / "manifest.csv").touch()

        report = qc_agent.qc_check(project_name)
        self.assertIn("Manifest is empty", report["failed"])

    def test_manifest_missing_fields(self):
        project_name = "MissingFieldsManifest"
        project_dir = self.setup_project(project_name)

        manifest_path = project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["item_number", "description"])
            writer.writeheader()
            writer.writerow({"item_number": "1", "description": "Test"})

        report = qc_agent.qc_check(project_name)
        self.assertIn("Manifest missing field: manufacturer", report["failed"])
        self.assertIn("Manifest missing field: model_number", report["failed"])
        self.assertIn("Manifest missing field: spec_section", report["failed"])

    def test_cover_sheet_warnings(self):
        project_name = "CoverWarnings"
        project_dir = self.setup_project(project_name)
        (project_dir / "01-cover").mkdir()
        cover_md = project_dir / "01-cover" / "cover-sheet.md"
        cover_md.write_text("This has ⚠️ and {{ another }}", encoding="utf-8")

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("unfilled placeholders" in w for w in report["warnings"]))
        self.assertTrue(any("may be missing spec sections" in w for w in report["warnings"]))

    def test_item_index_warnings(self):
        project_name = "IndexWarnings"
        project_dir = self.setup_project(project_name)
        (project_dir / "02-index").mkdir()

        manifest_path = project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["item_number"])
            writer.writeheader()
            writer.writerow({"item_number": "1"})

        index_md = project_dir / "02-index" / "item-index.md"
        # Since we filter out "Item" and "---", giving it "| Test |\n" gives 1 row
        index_md.write_text("| Header |\n", encoding="utf-8") # wait, qc_agent uses "Item" not in l and "---" not in l

        # let's write 0 rows instead, meaning manifest has 1, index has 0
        index_md.write_text("| Item |\n| --- |\n", encoding="utf-8")

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("Item index has 0 rows but manifest has 1 items" in w for w in report["warnings"]))

    def test_sequential_item_numbering_missing(self):
        project_name = "ItemNumMissing"
        project_dir = self.setup_project(project_name)
        items_dir = project_dir / "03-items"
        items_dir.mkdir()
        (items_dir / "Item-02").mkdir()

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("Missing item folders: Item-01" in f for f in report["failed"]))

    def test_sequential_item_numbering_extra(self):
        project_name = "ItemNumExtra"
        project_dir = self.setup_project(project_name)
        items_dir = project_dir / "03-items"
        items_dir.mkdir()
        (items_dir / "Item-01").mkdir()
        (items_dir / "Item-02").mkdir()
        (items_dir / "Item-03-Extra").mkdir()

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("Unexpected item folders" in w for w in report["warnings"]))

    def test_missing_separator(self):
        project_name = "MissingSeparator"
        project_dir = self.setup_project(project_name)

        manifest_path = project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["item_number"])
            writer.writeheader()
            writer.writerow({"item_number": "1"})

        items_dir = project_dir / "03-items"
        items_dir.mkdir()
        (items_dir / "Item-01").mkdir()

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("Item-01: No separator sheet" in f for f in report["failed"]))

    def test_missing_disclaimer(self):
        project_name = "MissingDisclaimer"
        project_dir = self.setup_project(project_name)

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("No disclaimer found" in w for w in report["warnings"]))

    def test_invalid_spec_format(self):
        project_name = "InvalidSpecFormat"
        project_dir = self.setup_project(project_name)

        manifest_path = project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["item_number", "spec_section"])
            writer.writeheader()
            writer.writerow({"item_number": "1", "spec_section": "12345"})

        report = qc_agent.qc_check(project_name)
        self.assertTrue(any("doesn't match CSI format XX XX XX" in w for w in report["warnings"]))

    def test_fully_compliant_project(self):
        project_name = "CompliantProject"
        project_dir = self.setup_project(project_name)

        # Create dirs
        for d in ["01-cover", "02-index", "03-items", "04-attachments"]:
            (project_dir / d).mkdir()

        # Create manifest
        manifest_path = project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["item_number", "description", "manufacturer", "model_number", "spec_section"])
            writer.writeheader()
            writer.writerow({
                "item_number": "1",
                "description": "Test Item",
                "manufacturer": "Test Mfg",
                "model_number": "TM-1",
                "spec_section": "22 00 00"
            })

        # Create cover sheet
        cover_md = project_dir / "01-cover" / "cover-sheet.md"
        cover_md.write_text("Spec Section 22", encoding="utf-8")

        # Create item index
        index_md = project_dir / "02-index" / "item-index.md"
        index_md.write_text("| 1 | Test | ... |\n", encoding="utf-8")

        # Create items dir and separator
        item_dir = project_dir / "03-items" / "Item-01"
        item_dir.mkdir()
        sep = item_dir / "separator.md"
        sep.write_text("Separator", encoding="utf-8")

        # Create disclaimer
        disclaimer = project_dir / "04-attachments" / "disclaimer.md"
        disclaimer.write_text("Disclaimer", encoding="utf-8")

        # Create package md
        pkg_md = project_dir / "SUBMITTAL-PACKAGE.md"
        pkg_md.write_text("No markers here", encoding="utf-8")

        report = qc_agent.qc_check(project_name)

        self.assertEqual(len(report["failed"]), 0, f"Failures: {report['failed']}")
        self.assertEqual(len(report["warnings"]), 0, f"Warnings: {report['warnings']}")
        self.assertEqual(report["score"], 100)

if __name__ == '__main__':
    unittest.main()
