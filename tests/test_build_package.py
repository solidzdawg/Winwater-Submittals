import unittest
import importlib.util
import sys
from pathlib import Path
import csv
import tempfile
import shutil

# Import build-package using importlib due to hyphen in filename
script_path = Path(__file__).resolve().parent.parent / "scripts" / "build-package.py"
spec = importlib.util.spec_from_file_location("build_package", script_path)
build_package = importlib.util.module_from_spec(spec)
sys.modules["build_package"] = build_package
spec.loader.exec_module(build_package)

class TestLoadManifest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as project_dir
        self.test_dir = Path(tempfile.mkdtemp())
        self.manifest_path = self.test_dir / "manifest.csv"

    def tearDown(self):
        # Remove the temporary directory after tests
        shutil.rmtree(self.test_dir)

    def test_load_manifest_happy_path(self):
        # Arrange
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["item_number", "description", "section_name"])
            writer.writerow(["1", "Test Item 1", "Section A"])
            writer.writerow(["2", "Test Item 2", "Section B"])

        # Act
        result = build_package.load_manifest(self.test_dir)

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["item_number"], "1")
        self.assertEqual(result[0]["description"], "Test Item 1")
        self.assertEqual(result[0]["section_name"], "Section A")
        self.assertEqual(result[1]["item_number"], "2")
        self.assertEqual(result[1]["description"], "Test Item 2")
        self.assertEqual(result[1]["section_name"], "Section B")

    def test_load_manifest_empty_csv(self):
        # Arrange
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["item_number", "description", "section_name"])
            # No data rows

        # Act
        result = build_package.load_manifest(self.test_dir)

        # Assert
        self.assertEqual(result, [])

    def test_load_manifest_missing_file(self):
        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            build_package.load_manifest(self.test_dir)

    def test_load_manifest_encoding(self):
        # Arrange
        # Using special characters to ensure utf-8 handling
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["item_number", "description", "section_name"])
            writer.writerow(["3", "Test 🚀 ñ", "Secção C"])

        # Act
        result = build_package.load_manifest(self.test_dir)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], "Test 🚀 ñ")
        self.assertEqual(result[0]["section_name"], "Secção C")

if __name__ == "__main__":
    unittest.main()
