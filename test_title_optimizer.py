import unittest
import logging
from title_optimizer import TitleOptimizer

# Disable logging during tests to keep the output clean
logging.disable(logging.CRITICAL)

class TestTitleOptimizer(unittest.TestCase):

    def setUp(self):
        """Set up a new TitleOptimizer instance before each test."""
        self.optimizer = TitleOptimizer()
        self.product_data = {
            "productId": "Minimalist_Band_Ring_V1",
            "material": "Gold",
            "colors": ["Yellow Gold", "White Gold", "Rose Gold"],
            "pricing": {
                "10K": 650.00,
                "14K": 780.00,
                "18K": 1100.00
            }
        }
        self.market_analysis = {
            "focus_keywords": ["Dainty Gold Ring", "Stacking Ring"],
            "secondary_keywords": ["Minimalist Jewelry", "Wedding Band"]
        }

    def test_execute_returns_correct_structure(self):
        """Test that the execute method returns a dictionary with the correct keys."""
        inputs = {"market_analysis": self.market_analysis, "product_data": self.product_data}
        result = self.optimizer.execute(inputs, {}, None)

        self.assertIsInstance(result, dict)
        self.assertIn("title_final", result)
        self.assertIn("title_variations", result)

    def test_final_title_is_valid(self):
        """Test that the selected final title adheres to all validation rules."""
        inputs = {"market_analysis": self.market_analysis, "product_data": self.product_data}
        result = self.optimizer.execute(inputs, {}, None)

        final_title = result.get("title_final")
        self.assertIsInstance(final_title, str)
        self.assertGreater(len(final_title), 0)

        # 1. Check length
        self.assertLessEqual(len(final_title), self.optimizer.MAX_LENGTH)

        # 2. Check for forbidden terms
        for term in self.optimizer.FORBIDDEN_TERMS:
            self.assertNotIn(term.lower(), final_title.lower())

        # 3. Check for mandatory content (at least one karat and color)
        has_karat = any(k.lower() in final_title.lower() for k in self.product_data["pricing"].keys())
        has_color = any(c.lower() in final_title.lower() for c in self.product_data["colors"])
        self.assertTrue(has_karat, "Final title should contain a karat value.")
        self.assertTrue(has_color, "Final title should contain a color value.")

    def test_front_loading_bonus_is_applied(self):
        """Test that a title with proper front-loading gets a higher score and is selected."""
        # This test assumes the primary template is well-formed for front-loading
        inputs = {"market_analysis": self.market_analysis, "product_data": self.product_data}
        result = self.optimizer.execute(inputs, {}, None)

        final_title = result.get("title_final")
        primary_keyword = self.market_analysis["focus_keywords"][0]

        # The best title should be the one generated from the primary template, which is front-loaded
        self.assertIn(primary_keyword, final_title)
        self.assertTrue(primary_keyword.lower() in final_title[:self.optimizer.FRONT_LOAD_CUTOFF].lower())

    def test_handles_missing_keywords(self):
        """Test that the module handles missing focus keywords gracefully."""
        inputs = {
            "market_analysis": {"focus_keywords": []},
            "product_data": self.product_data
        }
        result = self.optimizer.execute(inputs, {}, None)
        self.assertIn("Error", result["title_final"])

    def test_handles_incomplete_product_data(self):
        """Test that the module handles incomplete product data gracefully."""
        inputs = {
            "market_analysis": self.market_analysis,
            "product_data": {"material": "Gold"} # Missing pricing and colors
        }
        result = self.optimizer.execute(inputs, {}, None)
        self.assertIn("Error", result["title_final"])

if __name__ == '__main__':
    unittest.main()