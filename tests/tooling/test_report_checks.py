"""Missing, empty and failed reports cannot pass or expose raw payloads."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import check_test_report as reports


class ReportEvidence(unittest.TestCase):
    def test_reports_missing_empty_failed_or_all_skipped_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.xml"
            with self.assertRaises(FileNotFoundError):
                reports.inspect_report(path, True)
            for text in (
                "<testsuite/>",
                "<testsuite><system-out>private</system-out></testsuite>",
                "<broken>private",
                "<testsuite><testcase><skipped/></testcase></testsuite>",
                "<testsuite><testcase><failure>private</failure></testcase></testsuite>",
            ):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    reports.inspect_report(path, True)
                self.assertNotIn("private", path.read_text())
            path.write_text('<testsuite><testcase name="valid"/></testsuite>')
            self.assertEqual(reports.inspect_report(path), 1)
