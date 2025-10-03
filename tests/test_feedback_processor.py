import unittest
import os
import json
import pandas as pd
import shutil
from version_control import VersionControl

from feedback_processor import FeedbackProcessor
from knowledge_manager import KnowledgeManager

class TestFeedbackProcessor(unittest.TestCase):

    def setUp(self):
        """Set up test environment before each test."""
        self.perf_csv_path = "test_performance_data.csv"
        self.listing_json_path = "test_listing_history.json"

        # Setup VersionControl for KnowledgeManager
        self.version_config = {"pattern": "test_v{N}_{sha12}.json"}
        self.version_controller = VersionControl(self.version_config)

        # Create a dummy performance CSV
        perf_data = {
            'listing_id': [101, 102, 103],
            'date': ['2025-10-01', '2025-10-01', '2025-10-01'],
            'visits': [1500, 200, 50],
            'orders': [35, 1, 1],
            'ad_spend': [75.50, 15.00, 5.00],
            'revenue': [2500.00, 45.00, 45.00],
            'title': ["Gold Ring Set of 3", "Silver Band", "Plain Wedding Band"],
            'tags': ["gold ring,stacking ring", "silver band,wedding band", "minimalist ring,wedding band"]
        }
        pd.DataFrame(perf_data).to_csv(self.perf_csv_path, index=False)

        # Create a dummy listing history file (even if not fully used, for input correctness)
        with open(self.listing_json_path, 'w') as f:
            json.dump({"listing_id": 101, "title_at_publish": "Old Title"}, f)

    def tearDown(self):
        """Clean up test files after each test."""
        for path in [self.perf_csv_path, self.listing_json_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists("outputs"):
            shutil.rmtree("outputs")

    def test_execute_updates_knowledge_base(self):
        """
        Test that the execute method correctly processes performance data
        and adds the right insights to the knowledge base.
        """
        # Arrange
        km = KnowledgeManager(version_controller=self.version_controller, base_path="test_knowledge_base.json")
        processor = FeedbackProcessor()

        inputs = {
            "performance_data_csv": self.perf_csv_path,
            "listing_history_json": self.listing_json_path
        }

        # The context needs to provide the versioning config for the report saving
        context = {
            "fs": {
                "ver": self.version_config
            }
        }

        # Act
        result = processor.execute(inputs, context=context, knowledge_manager=km)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["insights_added"], 5, "Should have found 5 insights in total")

        # Verify the knowledge base content by reloading it
        km_reloaded = KnowledgeManager(version_controller=self.version_controller, base_path="test_knowledge_base.json")
        kb_data = km_reloaded.db
        self.assertEqual(len(kb_data["learned_insights"]), 5)

        insights = kb_data["learned_insights"]

        # Helper to find insights
        def find_insight(key, keyword=None):
            for i in insights:
                if i["key"] == key:
                    if keyword is None or (i["value"].get("keyword") == keyword):
                        return i
            return None

        def find_insights_by_keyword(keyword):
            return [i for i in insights if i["value"].get("keyword") == keyword]

        # Insight 1: Successful ROAS for "gold ring"
        gr_insight = find_insight("keyword_roas", "gold ring")
        self.assertIsNotNone(gr_insight)
        self.assertTrue(gr_insight["value"]["is_successful"])
        self.assertAlmostEqual(gr_insight["value"]["roas"], 33.11, places=2)
        self.assertEqual(gr_insight["source_id"], "FEEDBACK-LOOP-01")
        self.assertEqual(gr_insight["confidence"], 0.85)

        # Insight 2: Successful ROAS for "stacking ring"
        sr_insight = find_insight("keyword_roas", "stacking ring")
        self.assertIsNotNone(sr_insight)
        self.assertTrue(sr_insight["value"]["is_successful"])

        # Insight 3: Successful title structure (contains number)
        title_insight = find_insight("title_structure_contains_number")
        self.assertIsNotNone(title_insight)
        self.assertTrue(title_insight["value"]["is_successful"])
        self.assertAlmostEqual(title_insight["value"]["conversion_rate"], 0.0233, places=4)
        self.assertEqual(title_insight["confidence"], 0.90)

        # Insight 4: Successful ROAS for "silver band"
        sb_insight = find_insight("keyword_roas", "silver band")
        self.assertIsNotNone(sb_insight)
        self.assertTrue(sb_insight["value"]["is_successful"])
        self.assertAlmostEqual(sb_insight["value"]["roas"], 3.0, places=2)
        self.assertEqual(sb_insight["confidence"], 0.70)

        # Insight 5: Successful ROAS for "wedding band"
        # This keyword appears twice. We expect one successful insight from listing 102.
        wb_insights = find_insights_by_keyword("wedding band")
        self.assertEqual(len(wb_insights), 1)
        wb_insight = wb_insights[0]
        self.assertTrue(wb_insight["value"]["is_successful"])
        self.assertAlmostEqual(wb_insight["value"]["roas"], 3.0, places=2)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)