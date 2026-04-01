import unittest
import tempfile
from pathlib import Path
import os
import shutil
import importlib.util
import sys

# Add scripts directory to path to import assemble-submittal
scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.append(str(scripts_dir))

# Import assemble-submittal.py using importlib because of hyphen in name
spec = importlib.util.spec_from_file_location("assemble_submittal", scripts_dir / "assemble-submittal.py")
assemble_submittal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble_submittal)


class TestFindPdfsInDir(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_finds_pdfs_in_directory(self):
        # Setup: Create some dummy PDF files
        (self.test_path / "a.pdf").touch()
        (self.test_path / "c.pdf").touch()
        (self.test_path / "b.pdf").touch()

        # Action
        result = assemble_submittal.find_pdfs_in_dir(self.test_path)

        # Assert: Should return them sorted
        expected = [
            self.test_path / "a.pdf",
            self.test_path / "b.pdf",
            self.test_path / "c.pdf",
        ]
        self.assertEqual(result, expected)

    def test_ignores_non_pdf_files(self):
        # Setup: Create PDFs and other files
        (self.test_path / "doc.txt").touch()
        (self.test_path / "image.png").touch()
        (self.test_path / "valid.pdf").touch()

        # Action
        result = assemble_submittal.find_pdfs_in_dir(self.test_path)

        # Assert
        self.assertEqual(result, [self.test_path / "valid.pdf"])

    def test_returns_empty_list_for_empty_dir(self):
        # Action
        result = assemble_submittal.find_pdfs_in_dir(self.test_path)

        # Assert
        self.assertEqual(result, [])

    def test_returns_empty_list_for_nonexistent_dir(self):
        # Action
        nonexistent = self.test_path / "does_not_exist"
        result = assemble_submittal.find_pdfs_in_dir(nonexistent)

        # Assert
        self.assertEqual(result, [])

    def test_case_sensitivity(self):
        # Setup: Create a file with .PDF uppercase extension
        (self.test_path / "upper.PDF").touch()
        (self.test_path / "lower.pdf").touch()

        # Action
        result = assemble_submittal.find_pdfs_in_dir(self.test_path)

        # Assert: glob("*.pdf") is case-sensitive on Linux/Unix, but we should verify the expected behavior
        # Assuming the implementation is `directory.glob("*.pdf")`, it will not find upper.PDF on Linux
        self.assertEqual(result, [self.test_path / "lower.pdf"])

if __name__ == "__main__":
    unittest.main()
