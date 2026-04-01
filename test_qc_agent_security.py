import unittest
from pathlib import Path
from scripts.agents.qc_agent import qc_check

class TestQCAgentSecurity(unittest.TestCase):
    def test_path_traversal_blocked(self):
        """Test that paths pointing outside SUBMITTALS_DIR return a failure"""
        traversal_paths = [
            "../../etc/passwd",
            "../other_project",
            "/etc/passwd",
            "/absolute/path/somewhere",
            "Double-RR/../../../../etc/passwd",
        ]

        for p in traversal_paths:
            report = qc_check(p)
            self.assertIn("failed", report)
            self.assertTrue(
                any("path traversal detected" in f or "Invalid project name" in f for f in report["failed"]),
                f"Path {p} was not blocked correctly"
            )

    def test_valid_path_allowed(self):
        """Test that a valid project path continues without traversal error"""
        report = qc_check("Double-RR")
        # Ensure it doesn't fail with the traversal error
        self.assertFalse(
            any("path traversal detected" in f or "Invalid project name" in f for f in report["failed"]),
            "Valid project was incorrectly blocked"
        )
        # Note: It might still fail if "Double-RR" doesn't exist, but that's a regular failure, not a security one.

if __name__ == "__main__":
    unittest.main()
