import unittest
import os
import json
import tempfile
import shutil
import sys
from datetime import datetime, timezone, timedelta

# This is a bit of a hack to make sure we can import the modules from the root of the repo
# directly, which is required since the test is not part of a formal package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from knowledge_manager import KnowledgeManager
from version_control import VersionControl

class TestKnowledgeManager(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and fresh instances for each test."""
        self.temp_dir = tempfile.mkdtemp()

        # This mock config ensures all files created by VersionControl go into our temp dir
        mock_vc_config = {
            "pattern": "test_v{N}.json",
            "base_dir": self.temp_dir,
            "ver_dir": os.path.join(self.temp_dir, "ver"),
        }

        self.vc = VersionControl(versioning_config=mock_vc_config)
        self.db_base_path = 'kb/knowledge_base.json' # A logical path, not a real one

    def tearDown(self):
        """Remove the temporary directory and all its contents after each test."""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_no_db_file(self):
        """
        Test that the KM creates an initial, empty DB file if none exists.
        This is the most critical test for ensuring the KM starts correctly.
        """
        # Act: Initialize the KnowledgeManager. This should trigger the creation of the first DB file.
        km = KnowledgeManager(version_controller=self.vc, base_path=self.db_base_path)

        # Assert
        # 1. Check that a file was actually created by the version controller.
        latest_path = self.vc.get_latest_version_path(self.db_base_path)
        self.assertIsNotNone(latest_path, "KM should create a DB file on initialization if none exists.")
        self.assertTrue(os.path.exists(latest_path), f"Expected file to exist at {latest_path}")

        # 2. Check the content of the newly created file.
        with open(latest_path, 'r') as f:
            data = json.load(f)

        # 3. Verify it has the correct, empty structure.
        self.assertIn("session_state", data)
        self.assertIn("learned_insights", data)
        self.assertIn("performance_metrics", data)
        self.assertEqual(data["session_state"], {})
        self.assertEqual(data["learned_insights"], [])

    def test_add_and_get_insight(self):
        """Test adding a new insight and retrieving it."""
        km = KnowledgeManager(self.vc, self.db_base_path)
        km.add_insight("test_key", "test_value", "test_source", 0.9)

        # Create a new instance to ensure it loads from the saved file
        km_reloaded = KnowledgeManager(self.vc, self.db_base_path)
        insight = km_reloaded.get_latest_insight("test_key")

        self.assertIsNotNone(insight)
        self.assertEqual(insight['value'], "test_value")

    def test_get_latest_insight_returns_most_recent(self):
        """Test if get_latest_insight correctly returns the newest item."""
        km = KnowledgeManager(self.vc, self.db_base_path)
        km.add_insight("multi_key", "old_value", "source1", 0.8)
        # We need a slight delay to ensure timestamps are different for sorting
        import time; time.sleep(0.01)
        km.add_insight("multi_key", "new_value", "source2", 0.9)

        km_reloaded = KnowledgeManager(self.vc, self.db_base_path)
        insight = km_reloaded.get_latest_insight("multi_key")
        self.assertEqual(insight['value'], "new_value")

    def test_find_insights_by_source(self):
        """Test finding all insights from a specific source."""
        km = KnowledgeManager(self.vc, self.db_base_path)
        km.add_insight("key1", "val1", "source_A", 0.9)
        km.add_insight("key2", "val2", "source_B", 0.9)
        km.add_insight("key3", "val3", "source_A", 0.9)

        km_reloaded = KnowledgeManager(self.vc, self.db_base_path)
        source_a_insights = km_reloaded.find_insights_by_source("source_A")
        self.assertEqual(len(source_a_insights), 2)
        source_b_insights = km_reloaded.find_insights_by_source("source_B")
        self.assertEqual(len(source_b_insights), 1)

    def test_session_state(self):
        """Test setting and getting session state."""
        km = KnowledgeManager(self.vc, self.db_base_path)
        km.set_session_state("active_task", "KB-MGMT-01")

        km_reloaded = KnowledgeManager(self.vc, self.db_base_path)
        self.assertEqual(km_reloaded.get_session_state("active_task"), "KB-MGMT-01")

    def test_insight_expiration(self):
        """Test that expired insights are ignored by default."""
        # This KM instance will write an insight with a short TTL (expired yesterday)
        km_short_ttl = KnowledgeManager(self.vc, self.db_base_path, ttl_days=-1)
        km_short_ttl.add_insight("expired_key", "expired_value", "test_source", 1.0)

        # A new KM instance will load the latest DB from the version controller
        km_reopened = KnowledgeManager(self.vc, self.db_base_path, ttl_days=-1)
        insight = km_reopened.get_latest_insight("expired_key")
        self.assertIsNone(insight)

        # Test getting it with ignore_expired=False
        insight_not_ignored = km_reopened.get_latest_insight("expired_key", ignore_expired=False)
        self.assertIsNotNone(insight_not_ignored)
        self.assertEqual(insight_not_ignored['value'], "expired_value")

if __name__ == '__main__':
    unittest.main()