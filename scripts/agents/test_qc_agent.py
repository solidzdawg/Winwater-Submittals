import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from agents.qc_agent import qc_check, load_manifest

class TestQCAgent(unittest.TestCase):

    @patch('agents.qc_agent.SUBMITTALS_DIR')
    def test_qc_check_project_dir_not_exists(self, mock_submittals_dir):
        # Setup mock for missing project directory
        mock_project_dir = MagicMock()
        mock_project_dir.exists.return_value = False
        mock_submittals_dir.__truediv__.return_value = mock_project_dir

        # Execute the check
        report = qc_check("non_existent_project")

        # Verify failure is recorded and score is 0
        self.assertIn("Project directory does not exist", report["failed"])
        self.assertEqual(report["score"], 0)

    @patch('agents.qc_agent.SUBMITTALS_DIR')
    def test_qc_check_empty_manifest(self, mock_submittals_dir):
        # Setup mock project directory
        mock_project_dir = MagicMock()
        mock_project_dir.exists.return_value = True
        mock_submittals_dir.__truediv__.return_value = mock_project_dir

        # Helper to simulate file structure
        def mock_truediv(other):
            mock_path = MagicMock()
            if other == "manifest.csv":
                mock_path.exists.return_value = True
                mock_path.name = "manifest.csv"
            elif other in ["01-cover", "02-index", "03-items", "04-attachments"]:
                mock_path.exists.return_value = True
            elif other == "SUBMITTAL-PACKAGE.md":
                mock_path.exists.return_value = False
            else:
                mock_path.exists.return_value = False

            mock_path.read_text.return_value = ""
            mock_path.iterdir.return_value = []
            mock_path.__truediv__.side_effect = mock_truediv
            return mock_path

        mock_project_dir.__truediv__.side_effect = mock_truediv

        # Mock load_manifest to return empty list representing empty file
        with patch('agents.qc_agent.load_manifest') as mock_load_manifest:
            mock_load_manifest.return_value = []
            report = qc_check("test_project")

            self.assertIn("Manifest is empty", report["failed"])

    @patch('agents.qc_agent.SUBMITTALS_DIR')
    def test_qc_check_missing_manifest(self, mock_submittals_dir):
        # Setup mock project directory
        mock_project_dir = MagicMock()
        mock_project_dir.exists.return_value = True
        mock_submittals_dir.__truediv__.return_value = mock_project_dir

        # Helper to simulate file structure missing manifest.csv
        def mock_truediv(other):
            mock_path = MagicMock()
            if other == "manifest.csv":
                mock_path.exists.return_value = False
                mock_path.name = "manifest.csv"
            elif other in ["01-cover", "02-index", "03-items", "04-attachments"]:
                mock_path.exists.return_value = True
            elif other == "SUBMITTAL-PACKAGE.md":
                mock_path.exists.return_value = False
            else:
                mock_path.exists.return_value = False

            mock_path.read_text.return_value = ""
            mock_path.iterdir.return_value = []
            mock_path.__truediv__.side_effect = mock_truediv
            return mock_path

        mock_project_dir.__truediv__.side_effect = mock_truediv

        # Execute the check
        report = qc_check("test_project")

        self.assertIn("Manifest file missing", report["failed"])

    @patch('agents.qc_agent.SUBMITTALS_DIR')
    def test_qc_check_missing_cover_sheet(self, mock_submittals_dir):
        # Setup mock project directory
        mock_project_dir = MagicMock()
        mock_project_dir.exists.return_value = True
        mock_submittals_dir.__truediv__.return_value = mock_project_dir

        # Helper to simulate missing cover-sheet.md
        def mock_truediv(other):
            mock_path = MagicMock()
            if other == "manifest.csv":
                mock_path.exists.return_value = True
                mock_path.name = "manifest.csv"
            elif other in ["01-cover", "02-index", "03-items", "04-attachments"]:
                mock_path.exists.return_value = True
            elif other == "cover-sheet.md":
                mock_path.exists.return_value = False
            elif other == "SUBMITTAL-PACKAGE.md":
                mock_path.exists.return_value = False
            else:
                mock_path.exists.return_value = False

            mock_path.read_text.return_value = ""
            mock_path.iterdir.return_value = []
            mock_path.__truediv__.side_effect = mock_truediv
            return mock_path

        mock_project_dir.__truediv__.side_effect = mock_truediv

        # Execute the check with a dummy manifest row
        with patch('agents.qc_agent.load_manifest') as mock_load_manifest:
            mock_load_manifest.return_value = [{"item_number": "1", "description": "test", "manufacturer": "test", "model_number": "test", "spec_section": "22 00 00"}]
            report = qc_check("test_project")

            self.assertIn("No cover-sheet.md found (may be PDF only)", report["warnings"])

if __name__ == '__main__':
    unittest.main()
