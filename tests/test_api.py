import json
import unittest
from pathlib import Path
import sys
from urllib.parse import quote

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui.app import app


class TestSimulationAPI(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_json_response(self):
        resp = self.client.post(
            "/",
            data={"num_agents": 3, "days": 1},
            headers={"Accept": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("results", data)
        self.assertIn("agents", data)
        good = next(iter(data["results"]))
        self.assertIn("prices", data["results"][good])
        self.assertIn("volumes", data["results"][good])

    def test_step_and_reset(self):
        # Reset to ensure clean state
        resp = self.client.post("/reset", json={"num_agents": 2})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data["days"], 0)

        # Step one day
        resp = self.client.post("/step", json={"days": 1})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data["days"], 1)

        # Step another day and ensure day counter increases
        resp = self.client.post("/step", json={"days": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["days"], 2)

    def test_job_distribution(self):
        payload = {"days": 1, "job_Sand_Digger": 2, "job_Glass_Maker": 1}
        resp = self.client.post(
            "/", data=payload, headers={"Accept": "application/json"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        jobs = [agent["job"] for agent in data["agents"]]
        self.assertEqual(jobs.count("Sand Digger"), 2)
        self.assertEqual(jobs.count("Glass Maker"), 1)

    def test_overview_endpoint(self):
        resp = self.client.get("/overview", headers={"Accept": "application/json"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn("days_elapsed", data)
        self.assertIn("active_agents", data)

    def test_rebuild_endpoint(self):
        resp = self.client.post("/rebuild", json={"num_agents": 2})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data["days"], 0)

    def test_agent_detail_endpoint(self):
        resp = self.client.post("/reset", json={"num_agents": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        agent_name = data["agents"][0]["name"]
        url = "/agent/" + quote(agent_name)
        resp = self.client.get(url, headers={"Accept": "application/json"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        detail = resp.get_json()
        self.assertEqual(detail["name"], agent_name)
        self.assertIn("inventory", detail)


if __name__ == "__main__":
    unittest.main()
