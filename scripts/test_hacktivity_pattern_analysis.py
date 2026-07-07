import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

import hacktivity_pattern_analysis as hpa


class AnalyzeWeaknesses(unittest.TestCase):
    def test_counts_names_and_ids(self):
        weaknesses = [
            {"id": "1", "attributes": {"name": "XSS", "cwe": "CWE-79"}},
            {"id": "2", "attributes": {"name": "SQLi", "cwe": "CWE-89"}},
        ]
        out = hpa.analyze_weaknesses(weaknesses)
        self.assertEqual(out["total"], 2)
        self.assertEqual(out["names"], ["XSS", "SQLi"])
        self.assertEqual(out["weakness_ids"], ["1", "2"])


class AnalyzeHacktivity(unittest.TestCase):
    def test_counts_and_totals(self):
        items = [
            {"attributes": {"disclosed": True, "total_awarded_amount": 100, "severity_rating": "high", "cwe": "CWE-79", "title": "A"}},
            {"attributes": {"disclosed": False, "total_awarded_amount": 50, "severity_rating": "medium", "cwe": "CWE-89", "title": "B"}},
        ]
        out = hpa.analyze_hacktivity(items)
        self.assertEqual(out["total_items"], 2)
        self.assertEqual(out["disclosed_count"], 1)
        self.assertEqual(out["awarded_count"], 2)
        self.assertEqual(out["total_awarded"], 150.0)
        self.assertEqual(out["severity_counts"], {"high": 1, "medium": 1})
        self.assertEqual(out["weakness_counts"], {"CWE-79": 1, "CWE-89": 1})


class GetHacktivityForProgram(unittest.TestCase):
    @patch.object(hpa, "_build_evidence")
    def test_success(self, mock_evidence):
        with patch.object(hpa.h1, "hacktivity_program", return_value=[{"id": 1}]) as mock_hp:
            data = hpa._get_hacktivity_for_program("shopify")
        self.assertEqual(data, [{"id": 1}])
        mock_hp.assert_called_once_with(program_handle="shopify")
        mock_evidence.assert_not_called()

    @patch.object(hpa, "_build_evidence")
    def test_fallback_on_invalid_query(self, mock_evidence):
        err = RuntimeError('HTTP 400 for /v1/hackers/hacktivity?queryString=team:shopify: {"errors":[{"status":400,"title":"Invalid Query","detail":"Unable to parse ElasticSearch query","source":{"parameter":""}}]}')
        with patch.object(hpa.h1, "hacktivity_program", side_effect=err), \
             patch.object(hpa.h1, "hacktivity", return_value=[{"id": 2}]) as mock_global:
            data = hpa._get_hacktivity_for_program("shopify")
        self.assertEqual(data, [{"id": 2}])
        mock_global.assert_called_once()
        self.assertEqual(mock_evidence.call_count, 1)
        evidence_body = mock_evidence.call_args[0][4]
        self.assertEqual(evidence_body["fallback"], "global")
        self.assertEqual(evidence_body["filtered_by"], "shopify")

    @patch.object(hpa, "_build_evidence")
    def test_other_error_still_records(self, mock_evidence):
        err = RuntimeError("HTTP 500 for /v1/hackers/hacktivity")
        with patch.object(hpa.h1, "hacktivity_program", side_effect=err):
            data = hpa._get_hacktivity_for_program("basecamp")
        self.assertEqual(data, [])
        self.assertEqual(mock_evidence.call_count, 1)


if __name__ == "__main__":
    unittest.main()
