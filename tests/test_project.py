import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.policy import allowed, route


ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


class PolicyRoutingTests(unittest.TestCase):
    def test_low_impact_actions_can_be_auto_routed(self):
        self.assertEqual(route("MONITOR_CARD"), "auto")
        self.assertEqual(route("CLOSE_NO_FRAUD"), "auto")

    def test_high_impact_actions_require_l2(self):
        for action in (
            "DECLINE_TRANSACTION",
            "BLOCK_CARD",
            "FILE_REPORT",
            "ESCALATE_TO_ANALYST",
        ):
            with self.subTest(action=action):
                self.assertEqual(route(action), "L2")

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
        self.assertTrue(response.json()["case_store_ready"])

    def test_case_lookup(self):
        response = client.get("/case/HHG-001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["case_id"], "HHG-001")

    def test_case_lookup_is_case_insensitive(self):
        self.assertEqual(client.get("/case/hhg-001").status_code, 200)

    def test_missing_case_returns_404(self):
        self.assertEqual(client.get("/case/HHG-999").status_code, 404)

    def test_invalid_case_id_is_rejected(self):
        self.assertEqual(client.get("/case/../../etc/passwd").status_code, 404)
        response = client.post("/investigate", json={"case_id": "not-a-case"})
        self.assertEqual(response.status_code, 422)

    def test_investigation_normalizes_case_id_and_routes_actions(self):
        response = client.post("/investigate", json={"case_id": " hhg-003 "})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["case_id"], "HHG-003")
        self.assertEqual(payload["mode"], "benchmark-artifact-replay")
        self.assertFalse(payload["case_memory"]["written_to_graph"])
        self.assertIn("does not run live graph queries", payload["demo_note"])
        final_actions = payload["next_best_action"]["final"]
        block = next(item for item in final_actions if item["action"] == "BLOCK_CARD")
        self.assertEqual(block["approval"], "L2")

    def test_tigergraph_status_does_not_expose_host_or_token(self):
        response = client.get("/tg-status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn("host", body["tigergraph"])
        self.assertNotIn("token", body["tigergraph"])

    def test_case_id_whitespace_is_normalized(self):
        response = client.post("/investigate", json={"case_id": " HHG-001 "})
        self.assertEqual(response.status_code, 200)


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
                actions = data["next_best_actions"]
                self.assertIsInstance(actions.get("initial"), list)
                self.assertIsInstance(actions.get("final"), list)
                self.assertIsInstance(data["case"].get("evidence"), list)
                probability = data["case"].get("fraud_probability")
                self.assertIsInstance(probability, (int, float))
                self.assertGreaterEqual(probability, 0)
                self.assertLessEqual(probability, 1)


if __name__ == "__main__":
    unittest.main()
