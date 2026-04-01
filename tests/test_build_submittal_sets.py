import unittest
import importlib.util
from pathlib import Path
import json
import tempfile
import sys

# Load the script dynamically because of hyphens in the filename
spec = importlib.util.spec_from_file_location("build_submittal_sets", "scripts/build-submittal-sets.py")
build_submittal_sets = importlib.util.module_from_spec(spec)
sys.modules["build_submittal_sets"] = build_submittal_sets
spec.loader.exec_module(build_submittal_sets)

class TestLoadProjectConfig(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the project directory
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.test_dir.name)
        self.config_path = self.project_dir / "project.json"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_load_project_config_no_file(self):
        """Test behavior when project.json does not exist."""
        # Ensure the file doesn't exist
        if self.config_path.exists():
            self.config_path.unlink()

        project_info, submittal_sets = build_submittal_sets.load_project_config(self.project_dir)

        self.assertEqual(project_info, build_submittal_sets.DEFAULT_PROJECT_INFO)
        self.assertEqual(submittal_sets, build_submittal_sets.DEFAULT_SUBMITTAL_SETS)

    def test_load_project_config_with_file_no_submittal_sets(self):
        """Test behavior when project.json exists but lacks 'submittal_sets'."""
        config_data = {
            "project_name": "Test Project",
            "project_number": "12345",
            "to_company": "Test Company"
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        project_info, submittal_sets = build_submittal_sets.load_project_config(self.project_dir)

        self.assertEqual(project_info, config_data)
        self.assertEqual(submittal_sets, build_submittal_sets.DEFAULT_SUBMITTAL_SETS)

    def test_load_project_config_with_file_and_submittal_sets(self):
        """Test behavior when project.json exists and contains 'submittal_sets'."""
        custom_sets = [
            {"id": "01", "name": "Custom Set 1", "items": [1, 2], "spec": "00 00 00"}
        ]
        config_data = {
            "project_name": "Test Project",
            "submittal_sets": custom_sets
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        project_info, submittal_sets = build_submittal_sets.load_project_config(self.project_dir)

        # 'submittal_sets' should be removed from project_info
        expected_project_info = {"project_name": "Test Project"}
        self.assertEqual(project_info, expected_project_info)
        self.assertEqual(submittal_sets, custom_sets)

if __name__ == '__main__':
    unittest.main()
