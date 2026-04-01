import unittest
from unittest.mock import patch
import tempfile
import csv
from pathlib import Path
import os
import shutil

# Make sure we can import the agent
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agents.validate_agent import validate_project


class TestValidateAgent(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for our mock structure
        self.test_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.test_dir.name)
        self.submittals_dir = self.base_dir / "submittals"
        self.submittals_dir.mkdir()

        # Patch BASE_DIR and SUBMITTALS_DIR in the agent module
        self.patcher_base = patch('agents.validate_agent.BASE_DIR', self.base_dir)
        self.patcher_sub = patch('agents.validate_agent.SUBMITTALS_DIR', self.submittals_dir)
        self.patcher_base.start()
        self.patcher_sub.start()

        self.project_name = "Test-Project"
        self.project_dir = self.submittals_dir / self.project_name
        self.project_dir.mkdir()

    def tearDown(self):
        self.patcher_base.stop()
        self.patcher_sub.stop()
        self.test_dir.cleanup()

    def test_missing_project_directory(self):
        # Remove the project dir we created in setUp
        shutil.rmtree(self.project_dir)

        report = validate_project(self.project_name)
        self.assertFalse(report["ready"])
        self.assertEqual(len(report["errors"]), 1)
        self.assertIn("Project directory not found", report["errors"][0])

    def test_missing_required_directories(self):
        report = validate_project(self.project_name)
        self.assertFalse(report["ready"])
        # Should have errors for missing 01-cover, 02-index, 03-items, 04-attachments
        # plus the missing manifest error
        error_msgs = " ".join(report["errors"])
        self.assertIn("01-cover", error_msgs)
        self.assertIn("02-index", error_msgs)
        self.assertIn("03-items", error_msgs)
        self.assertIn("04-attachments", error_msgs)

    def test_empty_directories_warnings(self):
        # Create required dirs
        for dirname in ["01-cover", "02-index", "03-items", "04-attachments"]:
            (self.project_dir / dirname).mkdir()

        # Manifest is missing, but directories are empty, so we should get warnings
        report = validate_project(self.project_name)

        warnings = " ".join(report["warnings"])
        self.assertIn("01-cover/ exists but has no PDF or MD files", warnings)
        self.assertIn("02-index/ exists but has no PDF or MD files", warnings)
        self.assertIn("04-attachments/ exists but has no PDF or MD files", warnings)
        # 03-items is explicitly excluded from this warning check
        self.assertNotIn("03-items/ exists but has no PDF or MD files", warnings)

    def test_missing_or_empty_manifest(self):
        for dirname in ["01-cover", "02-index", "03-items", "04-attachments"]:
            (self.project_dir / dirname).mkdir()

        # Missing manifest
        report = validate_project(self.project_name)
        self.assertFalse(report["ready"])
        self.assertIn("Manifest is empty or missing", report["errors"])

        # Empty manifest
        manifest_path = self.project_dir / "manifest.csv"
        manifest_path.touch()
        report2 = validate_project(self.project_name)
        self.assertFalse(report2["ready"])
        self.assertIn("Manifest is empty or missing", report2["errors"])

    def create_valid_structure_with_manifest(self, rows):
        # Helper to setup a valid structure and a manifest
        for dirname in ["01-cover", "02-index", "03-items", "04-attachments"]:
            dir_path = self.project_dir / dirname
            dir_path.mkdir(exist_ok=True)
            # Add a dummy file so we don't get empty dir warnings
            if dirname != "03-items":
                (dir_path / "dummy.pdf").touch()

        manifest_path = self.project_dir / "manifest.csv"
        with open(manifest_path, 'w', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def test_missing_item_folder(self):
        self.create_valid_structure_with_manifest([
            {"item_number": "1", "description": "Test Item"}
        ])

        report = validate_project(self.project_name)
        self.assertFalse(report["ready"])
        self.assertIn("Item-01 folder missing", report["errors"])

    def test_missing_separator_and_cut_sheet_fallback(self):
        self.create_valid_structure_with_manifest([
            {"item_number": "2", "description": "Item 2"}
        ])
        item_folder = self.project_dir / "03-items" / "Item-02"
        item_folder.mkdir(parents=True)

        report = validate_project(self.project_name)

        warnings = " ".join(report["warnings"])
        self.assertIn("Item-02: No separator sheet", warnings)

        item_status = report["items"][0]
        self.assertFalse(item_status["separator"])
        self.assertFalse(item_status["cut_sheet"])

    def test_valid_separator_and_cut_sheet_fallback(self):
        self.create_valid_structure_with_manifest([
            {"item_number": "3", "description": "Item 3"}
        ])
        item_folder = self.project_dir / "03-items" / "Item-03"
        item_folder.mkdir(parents=True)

        # Create separator
        (item_folder / "separator.pdf").touch()
        # Create a non-separator pdf for fallback cut sheet check
        (item_folder / "cutsheet.pdf").touch()

        report = validate_project(self.project_name)

        item_status = report["items"][0]
        self.assertTrue(item_status["separator"])
        self.assertTrue(item_status["cut_sheet"])
        self.assertTrue(report["ready"])
        self.assertEqual(len(report["errors"]), 0)

    def test_cut_sheet_path_explicit(self):
        self.create_valid_structure_with_manifest([
            {"item_number": "4", "description": "Item 4", "cut_sheet_path": "vendor-docs/doc1.pdf"}
        ])
        item_folder = self.project_dir / "03-items" / "Item-04"
        item_folder.mkdir(parents=True)
        (item_folder / "separator.pdf").touch()

        # Without the doc existing
        report1 = validate_project(self.project_name)
        self.assertFalse(report1["items"][0]["cut_sheet"])
        self.assertIn("Item-04: Cut sheet not found — vendor-docs/doc1.pdf", " ".join(report1["warnings"]))

        # With the doc existing
        vendor_dir = self.base_dir / "vendor-docs"
        vendor_dir.mkdir()
        (vendor_dir / "doc1.pdf").touch()

        report2 = validate_project(self.project_name)
        self.assertTrue(report2["items"][0]["cut_sheet"])

    def test_certifications(self):
        self.create_valid_structure_with_manifest([
            {
                "item_number": "5",
                "cert_nsf61_path": "certs/nsf61.pdf",
                "cert_nsf372_path": "certs/nsf372.pdf",
                "other_certs": "certs/other1.pdf, certs/other2.pdf"
            }
        ])
        item_folder = self.project_dir / "03-items" / "Item-05"
        item_folder.mkdir(parents=True)
        (item_folder / "separator.pdf").touch()
        (item_folder / "cutsheet.pdf").touch()

        # Initially, none of these certs exist
        report1 = validate_project(self.project_name)
        warnings = " ".join(report1["warnings"])
        self.assertIn("Item-05: Cert not found — certs/nsf61.pdf", warnings)
        self.assertIn("Item-05: Cert not found — certs/nsf372.pdf", warnings)
        self.assertIn("Item-05: Cert not found — certs/other1.pdf", warnings)
        self.assertIn("Item-05: Cert not found — certs/other2.pdf", warnings)
        self.assertEqual(len(report1["items"][0]["missing_certs"]), 4)

        # Create one cert
        certs_dir = self.base_dir / "certs"
        certs_dir.mkdir()
        (certs_dir / "nsf61.pdf").touch()

        report2 = validate_project(self.project_name)
        item2 = report2["items"][0]
        self.assertIn("NSF 61", item2["certs"])
        self.assertEqual(len(item2["missing_certs"]), 3)

    def test_fully_valid_project(self):
        self.create_valid_structure_with_manifest([
            {
                "item_number": "1",
                "description": "Valid Item",
                "cut_sheet_path": "vendor-docs/valid.pdf",
                "cert_nsf61_path": "certs/valid_nsf.pdf"
            }
        ])

        item_folder = self.project_dir / "03-items" / "Item-01"
        item_folder.mkdir(parents=True)
        (item_folder / "separator.pdf").touch()

        # Create dependencies
        (self.base_dir / "vendor-docs").mkdir(exist_ok=True)
        (self.base_dir / "certs").mkdir(exist_ok=True)
        (self.base_dir / "vendor-docs" / "valid.pdf").touch()
        (self.base_dir / "certs" / "valid_nsf.pdf").touch()

        report = validate_project(self.project_name)

        self.assertTrue(report["ready"])
        self.assertEqual(len(report["errors"]), 0)
        self.assertEqual(len(report["warnings"]), 0)

        item_status = report["items"][0]
        self.assertTrue(item_status["separator"])
        self.assertTrue(item_status["cut_sheet"])
        self.assertIn("NSF 61", item_status["certs"])
        self.assertEqual(len(item_status["missing_certs"]), 0)

if __name__ == '__main__':
    unittest.main()
