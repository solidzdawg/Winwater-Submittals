import unittest
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import importlib

# Have to use importlib since the filename has dashes
build_script = importlib.import_module("build-submittal-sets")


class TestLoConvert(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)
        self.input_path = Path(self.temp_dir) / "test_file.docx"
        self.input_path.touch()

        # Reset LO_BIN
        build_script.LO_BIN = None

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_lo_convert_timeout(self):
        with patch.object(build_script, 'find_libreoffice') as mock_find_lo, \
             patch.object(build_script.subprocess, 'run') as mock_run:

            mock_find_lo.return_value = "mock_libreoffice"
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["mock_libreoffice"], timeout=120)

            result = build_script.lo_convert(self.input_path, self.output_dir)

            self.assertIsNone(result)

    def test_lo_convert_filenotfound(self):
        with patch.object(build_script, 'find_libreoffice') as mock_find_lo, \
             patch.object(build_script.subprocess, 'run') as mock_run:

            mock_find_lo.return_value = "mock_libreoffice"
            mock_run.side_effect = FileNotFoundError()

            result = build_script.lo_convert(self.input_path, self.output_dir)

            self.assertIsNone(result)

    def test_lo_convert_success(self):
        with patch.object(build_script, 'find_libreoffice') as mock_find_lo, \
             patch.object(build_script.subprocess, 'run') as mock_run:

            mock_find_lo.return_value = "mock_libreoffice"

            # Create a mock pdf output
            pdf_path = self.output_dir / "test_file.pdf"
            pdf_path.touch()

            # Write some dummy bytes
            pdf_path.write_bytes(b'dummy pdf data')

            # Mock the process result
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "mock stdout"
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            result = build_script.lo_convert(self.input_path, self.output_dir)

            self.assertEqual(result, pdf_path)

    def test_lo_convert_fallback_match(self):
        with patch.object(build_script, 'find_libreoffice') as mock_find_lo, \
             patch.object(build_script.subprocess, 'run') as mock_run:

            mock_find_lo.return_value = "mock_libreoffice"

            # Create a mock pdf output with an alternate name matching the stem
            # The test will use test_file as stem
            pdf_path = self.output_dir / "some_prefix_test_file_suffix.pdf"
            pdf_path.touch()

            # Mock the process result
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "mock stdout"
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            result = build_script.lo_convert(self.input_path, self.output_dir)

            self.assertEqual(result, pdf_path)

    def test_lo_convert_no_output(self):
        with patch.object(build_script, 'find_libreoffice') as mock_find_lo, \
             patch.object(build_script.subprocess, 'run') as mock_run:

            mock_find_lo.return_value = "mock_libreoffice"

            # No pdf created

            # Mock the process result
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stdout = "mock stdout"
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            result = build_script.lo_convert(self.input_path, self.output_dir)

            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
