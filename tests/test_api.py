import json
import unittest
from pathlib import Path
import sys

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui.app import app

class TestSimulationAPI(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_json_response(self):
        resp = self.client.post('/', data={'num_agents': 3, 'days': 1}, headers={'Accept': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertIn('results', data)
        self.assertIn('agents', data)
        good = next(iter(data['results']))
        self.assertIn('prices', data['results'][good])
        self.assertIn('volumes', data['results'][good])

    def test_step_and_reset(self):
        # Reset to ensure clean state
        resp = self.client.post('/reset', json={'num_agents': 2})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data['days'], 0)

        # Step one day
        resp = self.client.post('/step', json={'days': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data['days'], 1)

        # Step another day and ensure day counter increases
        resp = self.client.post('/step', json={'days': 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['days'], 2)

    def test_job_distribution(self):
        payload = {
            'days': 1,
            'job_Sand_Digger': 2,
            'job_Glass_Maker': 1
        }
        resp = self.client.post('/', data=payload,
                               headers={'Accept': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        jobs = [agent['job'] for agent in data['agents']]
        self.assertEqual(jobs.count('Sand Digger'), 2)
        self.assertEqual(jobs.count('Glass Maker'), 1)

if __name__ == '__main__':
    unittest.main()
