import unittest
import importlib.util
from pathlib import Path
import sys
import tempfile
import csv

# Import the module
spec = importlib.util.spec_from_file_location("build_package", str(Path(__file__).parent / "build-package.py"))
build_package = importlib.util.module_from_spec(spec)
sys.modules["build_package"] = build_package
spec.loader.exec_module(build_package)

class TestLoadManifest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_manifest_happy_path(self):
        # Create a mock manifest.csv
        manifest_path = self.project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["section_name", "item_number", "description", "manufacturer"])
            writer.writerow(["Plumbing", "1", "Pipe", "ACME"])
            writer.writerow(["Electrical", "2", "Wire", "Beta"])

        # Call load_manifest
        result = build_package.load_manifest(self.project_dir)

        # Verify
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["section_name"], "Plumbing")
        self.assertEqual(result[0]["item_number"], "1")
        self.assertEqual(result[0]["description"], "Pipe")
        self.assertEqual(result[0]["manufacturer"], "ACME")

        self.assertEqual(result[1]["section_name"], "Electrical")
        self.assertEqual(result[1]["item_number"], "2")
        self.assertEqual(result[1]["description"], "Wire")
        self.assertEqual(result[1]["manufacturer"], "Beta")

    def test_load_manifest_empty_file(self):
        manifest_path = self.project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            pass # completely empty

        result = build_package.load_manifest(self.project_dir)
        self.assertEqual(result, [])

    def test_load_manifest_only_headers(self):
        manifest_path = self.project_dir / "manifest.csv"
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["section_name", "item_number"])

        result = build_package.load_manifest(self.project_dir)
        self.assertEqual(result, [])

    def test_load_manifest_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            build_package.load_manifest(self.project_dir)

if __name__ == "__main__":
    unittest.main()
