from pathlib import Path
import tempfile
import unittest

from conflux_audit.audit import audit_repo

class AuditTests(unittest.TestCase):
    def test_empty_repo_reports_missing_readme_and_tests(self):
        with tempfile.TemporaryDirectory() as d:
            result = audit_repo(d)
            rules = {f.rule for f in result.findings}
            self.assertIn("DOC-001", rules)
            self.assertIn("TEST-001", rules)

    def test_good_repo_has_no_structural_errors(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text("# Demo\n\n" + "Useful documentation. " * 30, encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/test.yml").write_text("name: test\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests/test_demo.py").write_text("def test_demo(): assert True\n", encoding="utf-8")
            result = audit_repo(root)
            self.assertEqual(result.errors, 0)

    def test_strong_claim_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text("# Demo\n\n" + "Useful documentation. " * 30 + "\nTests: 100% pass\n", encoding="utf-8")
            (root / "test_demo.py").write_text("def test_demo(): assert True\n", encoding="utf-8")
            result = audit_repo(root)
            self.assertTrue(any(f.rule == "EVID-001" for f in result.findings))

if __name__ == "__main__":
    unittest.main()
