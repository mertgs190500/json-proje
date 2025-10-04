import unittest
from unittest.mock import create_autospec
import os
import sys
import tempfile
import shutil
import json

# Add project root to path to allow direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from market_analyzer import MarketAnalyzer
from version_control import VersionControl

class TestMarketAnalyzerStep7a(unittest.TestCase):

    def setUp(self):
        """Set up a new MarketAnalyzer instance and mock objects for each test."""
        self.analyzer = MarketAnalyzer()
        self.temp_dir = tempfile.mkdtemp()

        # This mock config ensures all files created by VersionControl go into our temp dir
        mock_vc_config = {
            "pattern": "test_v{N}.json",
            "base_dir": self.temp_dir,
            "ver_dir": os.path.join(self.temp_dir, "ver"),
        }

        # We use a real VersionControl instance pointing to a temp directory
        # to ensure the interaction between modules is tested correctly.
        self.vc = VersionControl(versioning_config=mock_vc_config)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_execute_step_7a_full_functionality(self):
        """
        Tests the successful execution of step 7a with valid inputs, checking
        the analysis summary and the structure of the recommended pricing tiers.
        """
        # --- Arrange ---
        # 1. Mock the 'inputs' from the previous step (market analysis)
        mock_inputs = {
            "competitor_signals": {
                "pricing": {
                    "avg_price": 450.50,
                    "median_price": 425.00,
                }
            }
        }

        # 2. Mock the 'context' containing product information
        mock_context = {
            "product.info": {
                "variation_prices": {
                    "14K Gold": "$500",
                    "18K Gold": "$650"
                }
            }
        }

        # --- Act ---
        result = self.analyzer.execute_step_7a(mock_inputs, mock_context, self.vc)

        # --- Assert ---
        # 1. Assert that the function returns the expected dictionary from the save call
        self.assertIn("filepath", result)
        self.assertTrue(os.path.exists(result['filepath']))

        # 2. Read the saved data to verify its content
        with open(result['filepath'], 'r') as f:
            saved_data = json.load(f)

        self.assertIn("analysis_summary", saved_data)
        self.assertIn("recommended_tiers", saved_data)

        # 3. Check the values in the analysis summary
        summary = saved_data['analysis_summary']
        self.assertEqual(summary['competitor_price_avg'], 450.50)
        self.assertEqual(summary['competitor_price_median'], 425.00)

        # 4. Check the generated pricing tiers
        tiers = saved_data['recommended_tiers']
        self.assertIn("14K_Gold", tiers)
        self.assertEqual(len(tiers["14K_Gold"]), 3)

        competitive_tier = tiers["14K_Gold"][0]
        self.assertEqual(competitive_tier['tier'], 'Competitive')
        self.assertEqual(competitive_tier['price_usd'], 403) # 425 * 0.95
        self.assertIn("$425.00", competitive_tier['rationale'])

    def test_execute_step_7a_handles_missing_data(self):
        """
        Tests that the function raises a ValueError when essential data
        like pricing or product info is missing.
        """
        # --- Arrange ---
        # Case 1: Missing pricing data in inputs
        with self.assertRaises(ValueError):
            self.analyzer.execute_step_7a({}, {"product.info": {}}, self.vc)

        # Case 2: Missing product info in context
        mock_inputs = {"competitor_signals": {"pricing": {"median_price": 100}}}
        with self.assertRaises(ValueError):
            self.analyzer.execute_step_7a(mock_inputs, {}, self.vc)

if __name__ == '__main__':
    unittest.main()