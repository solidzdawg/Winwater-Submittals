import unittest
from pathlib import Path
import tempfile
import importlib.util
import logging
import io
import sys
import contextlib

# Import the script
spec = importlib.util.spec_from_file_location("build_package", "scripts/build-package.py")
build_package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_package)

class TestBuildPackage(unittest.TestCase):
    def test_count_pdf_pages_empty_or_corrupted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Test non-existent file
            non_existent_file = tmpdir_path / "does_not_exist.pdf"
            self.assertEqual(build_package.count_pdf_pages(non_existent_file), 0)

            # Test empty file
            empty_file = tmpdir_path / "empty.pdf"
            empty_file.touch()

            logger = logging.getLogger("pypdf")
            old_level = logger.level
            logger.setLevel(logging.CRITICAL)

            # PyPDF prints directly to sys.stderr for some errors so suppress it
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(build_package.count_pdf_pages(empty_file), 0)

                # Test corrupted PDF file
                corrupted_file = tmpdir_path / "corrupted.pdf"
                corrupted_file.write_text("This is not a valid PDF file content.")
                self.assertEqual(build_package.count_pdf_pages(corrupted_file), 0)

            logger.setLevel(old_level)

    def test_count_pdf_pages_valid(self):
        import weasyprint
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Test valid 1-page PDF
            valid_file_1 = tmpdir_path / "valid_1.pdf"
            weasyprint.HTML(string="<html><body><h1>Test Page 1</h1></body></html>").write_pdf(str(valid_file_1))
            self.assertEqual(build_package.count_pdf_pages(valid_file_1), 1)

            # Test valid 2-page PDF
            valid_file_2 = tmpdir_path / "valid_2.pdf"
            html_content = "<html><body><h1>Test Page 1</h1><div style='page-break-after: always;'></div><h1>Test Page 2</h1></body></html>"
            weasyprint.HTML(string=html_content).write_pdf(str(valid_file_2))
            self.assertEqual(build_package.count_pdf_pages(valid_file_2), 2)

if __name__ == '__main__':
    unittest.main()
