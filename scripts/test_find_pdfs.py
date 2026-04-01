import importlib.util
import sys
from pathlib import Path
import unittest
import tempfile

# Define the path to the script
SCRIPT_DIR = Path(__file__).parent
script_path = SCRIPT_DIR / "assemble-submittal.py"

# Load the module
spec = importlib.util.spec_from_file_location("assemble_submittal", script_path)
assemble_submittal = importlib.util.module_from_spec(spec)
sys.modules["assemble_submittal"] = assemble_submittal
spec.loader.exec_module(assemble_submittal)

class TestFindPdfsInDir(unittest.TestCase):
    def test_directory_does_not_exist(self):
        non_existent_dir = Path("/path/that/does/not/exist/ever")
        result = assemble_submittal.find_pdfs_in_dir(non_existent_dir)
        self.assertEqual(result, [])

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = assemble_submittal.find_pdfs_in_dir(Path(tmpdir))
            self.assertEqual(result, [])

    def test_only_pdfs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            pdf1 = dir_path / "a.pdf"
            pdf2 = dir_path / "b.pdf"
            pdf1.touch()
            pdf2.touch()

            result = assemble_submittal.find_pdfs_in_dir(dir_path)
            self.assertEqual(result, [pdf1, pdf2])

    def test_mixed_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            pdf1 = dir_path / "doc1.pdf"
            txt1 = dir_path / "doc1.txt"
            pdf2 = dir_path / "doc2.pdf"
            csv1 = dir_path / "data.csv"

            pdf1.touch()
            txt1.touch()
            pdf2.touch()
            csv1.touch()

            result = assemble_submittal.find_pdfs_in_dir(dir_path)
            self.assertEqual(result, [pdf1, pdf2])

    def test_sorting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir)
            pdf3 = dir_path / "z.pdf"
            pdf1 = dir_path / "a.pdf"
            pdf2 = dir_path / "m.pdf"

            # Touch in different order
            pdf3.touch()
            pdf2.touch()
            pdf1.touch()

            result = assemble_submittal.find_pdfs_in_dir(dir_path)
            self.assertEqual(result, [pdf1, pdf2, pdf3])

if __name__ == '__main__':
    unittest.main()
