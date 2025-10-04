import unittest
import os
import json
from datetime import datetime, timezone, timedelta
from knowledge_manager import KnowledgeManager

class TestKnowledgeManager(unittest.TestCase):

    def setUp(self):
        """Set up a temporary test database before each test."""
        self.test_db_path = 'test_knowledge_base.json'
        # Clean up any old test db file before starting
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.km = KnowledgeManager(db_path=self.test_db_path, ttl_days=30)

    def tearDown(self):
        """Remove the temporary test database after each test."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_initialization_creates_structured_db(self):
        """Test if a new, structured database is created if one doesn't exist."""
        self.assertTrue(os.path.exists(self.test_db_path))
        with open(self.test_db_path, 'r') as f:
            data = json.load(f)
        self.assertIn("session_state", data)
        self.assertIn("learned_insights", data)
        self.assertIn("performance_metrics", data)
        self.assertEqual(data["learned_insights"], [])

    def test_add_and_get_insight(self):
        """Test adding a new insight and retrieving it."""
        self.km.add_insight("test_key", "test_value", "test_source", 0.9)
        insight = self.km.get_latest_insight("test_key")
        self.assertIsNotNone(insight)
        self.assertEqual(insight['key'], "test_key")
        self.assertEqual(insight['value'], "test_value")
        self.assertEqual(insight['source_id'], "test_source")
        self.assertEqual(insight['confidence'], 0.9)
        self.assertIn("timestamp", insight)

    def test_get_latest_insight_returns_most_recent(self):
        """Test if get_latest_insight correctly returns the newest item."""
        self.km.add_insight("multi_key", "old_value", "source1", 0.8)
        # We need a slight delay to ensure timestamps are different
        import time; time.sleep(0.01)
        self.km.add_insight("multi_key", "new_value", "source2", 0.9)

        insight = self.km.get_latest_insight("multi_key")
        self.assertEqual(insight['value'], "new_value")
        self.assertEqual(insight['source_id'], "source2")

    def test_find_insights_by_source(self):
        """Test finding all insights from a specific source."""
        self.km.add_insight("key1", "val1", "source_A", 0.9)
        self.km.add_insight("key2", "val2", "source_B", 0.9)
        self.km.add_insight("key3", "val3", "source_A", 0.9)

        source_a_insights = self.km.find_insights_by_source("source_A")
        self.assertEqual(len(source_a_insights), 2)
        source_b_insights = self.km.find_insights_by_source("source_B")
        self.assertEqual(len(source_b_insights), 1)
        source_c_insights = self.km.find_insights_by_source("source_C")
        self.assertEqual(len(source_c_insights), 0)

    def test_session_state(self):
        """Test setting and getting session state."""
        self.km.set_session_state("active_task", "KB-MGMT-ADVANCED-01")
        active_task = self.km.get_session_state("active_task")
        self.assertEqual(active_task, "KB-MGMT-ADVANCED-01")

        full_state = self.km.get_session_state()
        self.assertIn("active_task", full_state)
        self.assertEqual(full_state["active_task"], "KB-MGMT-ADVANCED-01")

    def test_insight_expiration(self):
        """Test that expired insights are ignored by default."""
        km_short_ttl = KnowledgeManager(db_path=self.test_db_path, ttl_days=-1) # Expired yesterday
        km_short_ttl.add_insight("expired_key", "expired_value", "test_source", 1.0)

        # Re-open the DB with a manager that will see the entry as expired
        km_reopened = KnowledgeManager(db_path=self.test_db_path, ttl_days=-1)
        insight = km_reopened.get_latest_insight("expired_key")
        self.assertIsNone(insight)

        # Test getting it with ignore_expired=False
        insight_not_ignored = km_reopened.get_latest_insight("expired_key", ignore_expired=False)
        self.assertIsNotNone(insight_not_ignored)
        self.assertEqual(insight_not_ignored['value'], "expired_value")

if __name__ == '__main__':
    unittest.main()