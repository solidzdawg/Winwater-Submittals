import unittest
from agents.separator_agent import determine_certs

class TestSeparatorAgent(unittest.TestCase):
    def test_determine_certs_empty(self):
        row = {}
        certs = determine_certs(row)
        self.assertEqual(certs, [])

    def test_determine_certs_cut_sheet(self):
        row = {"cut_sheet_path": "path/to/cut_sheet.pdf"}
        certs = determine_certs(row)
        self.assertIn("Product Data / Cut Sheet", certs)
        self.assertEqual(len(certs), 1)

    def test_determine_certs_nsf61(self):
        row = {"cert_nsf61_path": "path/to/nsf61.pdf"}
        certs = determine_certs(row)
        self.assertIn("NSF 61 Certification", certs)
        self.assertEqual(len(certs), 1)

    def test_determine_certs_nsf372(self):
        row = {"cert_nsf372_path": "path/to/nsf372.pdf"}
        certs = determine_certs(row)
        self.assertIn("NSF 372 (Lead-Free) Certification", certs)
        self.assertEqual(len(certs), 1)

    def test_determine_certs_multiple(self):
        row = {
            "cut_sheet_path": "path/to/cut_sheet.pdf",
            "cert_nsf61_path": "path/to/nsf61.pdf",
            "cert_nsf372_path": "path/to/nsf372.pdf"
        }
        certs = determine_certs(row)
        self.assertIn("Product Data / Cut Sheet", certs)
        self.assertIn("NSF 61 Certification", certs)
        self.assertIn("NSF 372 (Lead-Free) Certification", certs)
        self.assertEqual(len(certs), 3)

if __name__ == '__main__':
    unittest.main()
