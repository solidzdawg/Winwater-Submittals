import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add scripts directory to path to allow importing orchestrator
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from orchestrator import step_validate

class TestOrchestrator(unittest.TestCase):

    @patch('orchestrator.validate_project')
    @patch('orchestrator.print_report')
    def test_step_validate_ready(self, mock_print_report, mock_validate_project):
        """Test step_validate when the project is ready."""
        # Setup mock return value
        mock_report = {"ready": True, "errors": [], "warnings": [], "items": []}
        mock_validate_project.return_value = mock_report

        # Call the function
        result = step_validate("DummyProject")

        # Assertions
        self.assertTrue(result)
        mock_validate_project.assert_called_once_with("DummyProject")
        mock_print_report.assert_called_once_with(mock_report)

    @patch('orchestrator.validate_project')
    @patch('orchestrator.print_report')
    def test_step_validate_not_ready(self, mock_print_report, mock_validate_project):
        """Test step_validate when the project is not ready."""
        # Setup mock return value
        mock_report = {"ready": False, "errors": ["Some error"], "warnings": [], "items": []}
        mock_validate_project.return_value = mock_report

        # Call the function
        result = step_validate("DummyProject")

        # Assertions
        self.assertFalse(result)
        mock_validate_project.assert_called_once_with("DummyProject")
        mock_print_report.assert_called_once_with(mock_report)

if __name__ == '__main__':
    unittest.main()
