import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.policy import allowed, route


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


class PolicyRoutingTests(unittest.TestCase):
    def test_escalation_requires_analyst_route(self):
        self.assertEqual(route("ESCALATE_TO_ANALYST"), "L2")

    def test_report_requires_analyst_route(self):
        self.assertEqual(route("FILE_REPORT"), "L2")

    def test_decline_requires_l1(self):
        self.assertEqual(route("DECLINE_TRANSACTION"), "L1")

    def test_card_block_route_uses_exposure(self):
        self.assertEqual(route("BLOCK_CARD", 2500), "L1")
        self.assertEqual(route("BLOCK_CARD", 2500.01), "L2")

    def test_unknown_action_is_not_marked_supported(self):
        result = allowed("RUN_ARBITRARY_ACTION")
        self.assertFalse(result["supported"])
        self.assertEqual(result["route"], "L2")


class ApiSmokeTests(unittest.TestCase):
    def test_root_and_health(self):
        self.assertEqual(client.get("/").status_code, 200)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["available_cases"], 20)

    def test_case_lookup(self):
        response = client.get("/case/HHG-001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["case_id"], "HHG-001")

    def test_case_lookup_is_case_insensitive(self):
        self.assertEqual(client.get("/case/hhg-001").status_code, 200)

    def test_missing_case_returns_404(self):
        self.assertEqual(client.get("/case/HHG-999").status_code, 404)

    def test_investigation_returns_routes_and_artifact_notice(self):
        response = client.post("/investigate", json={"case_id": "HHG-001"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["case_id"], "HHG-001")
        self.assertFalse(payload["case_memory"]["written_to_graph"])
        self.assertIn("Benchmark-grounded", payload["demo_note"])
        self.assertTrue(payload["next_best_action"]["final"])


class BenchmarkArtifactTests(unittest.TestCase):
    def test_all_twenty_case_files_exist_and_parse(self):
        cases_dir = ROOT / "cases"
        files = sorted(cases_dir.glob("HHG-*.json"))
        self.assertEqual(len(files), 20)
        for path in files:
            with self.subTest(case=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["case_id"], path.stem)
                self.assertIsInstance(data["case"], dict)
                self.assertIn("next_best_actions", data)


if __name__ == "__main__":
    unittest.main()
