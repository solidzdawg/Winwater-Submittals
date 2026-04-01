import unittest
from scripts.agents.vendor_fetch_agent import check_vendor_files

class TestVendorFetchAgent(unittest.TestCase):
    def test_path_traversal_blocked(self):
        with self.assertRaises(ValueError) as context:
            check_vendor_files("../../../../etc")

        self.assertIn("Access denied: Path traversal detected.", str(context.exception))

    def test_absolute_path_blocked(self):
        with self.assertRaises(ValueError) as context:
            check_vendor_files("/etc/passwd")

        self.assertIn("Access denied: Path traversal detected.", str(context.exception))

    def test_normal_access_permitted(self):
        try:
            # We assume Double-RR exists as a test project, or at least that it doesn't throw a ValueError for access
            check_vendor_files("Double-RR")
        except ValueError:
            self.fail("check_vendor_files raised ValueError unexpectedly!")

if __name__ == '__main__':
    unittest.main()
