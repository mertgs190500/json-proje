import unittest
import logging
from description_generator import DescriptionGenerator

# Disable logging during tests for cleaner output
logging.disable(logging.CRITICAL)

class TestDescriptionGenerator(unittest.TestCase):

    def setUp(self):
        """Set up a new DescriptionGenerator instance and mock data before each test."""
        self.generator = DescriptionGenerator()
        
        # Mock inputs mimicking the orchestrator's context
        self.product_data = {
            "materials": ["14K Gold", "Moissanite"],
            "pricing_by_karat": {"10K": "450", "14K": "650", "18K": "900"},
            "sizes_us": "US 4 – 14¾"
        }
        self.market_analysis = {
            "focus_keywords": ["Handmade Gold Ring", "Engagement Ring"],
            "secondary_keywords": ["Minimalist Jewelry", "Wedding Band"]
        }
        self.final_title = "Dainty Gold Ring | 14K Solid Gold Stacking Ring"

    def test_execute_returns_correct_structure(self):
        """Test that the execute method returns a dictionary with the correct keys."""
        inputs = {
            "market_analysis_results": self.market_analysis,
            "title_final": self.final_title,
            "product_data": self.product_data
        }
        result = self.generator.execute(inputs, {}, None)

        self.assertIsInstance(result, dict)
        self.assertIn("description_final", result)
        self.assertIn("validation_report", result)

    def test_description_is_generated(self):
        """Test that a non-empty description string is generated."""
        inputs = {
            "market_analysis_results": self.market_analysis,
            "title_final": self.final_title,
            "product_data": self.product_data
        }
        result = self.generator.execute(inputs, {}, None)
        self.assertIsInstance(result['description_final'], str)
        self.assertGreater(len(result['description_final']), 0)

    def test_validation_report_structure(self):
        """Test that the validation report has the correct structure and keys."""
        inputs = {
            "market_analysis_results": self.market_analysis,
            "title_final": self.final_title,
            "product_data": self.product_data
        }
        result = self.generator.execute(inputs, {}, None)
        report = result['validation_report']
        
        self.assertIsInstance(report, dict)
        self.assertIn("overall_status", report)
        self.assertIn("checks", report)
        self.assertIsInstance(report['checks'], list)
        self.assertTrue(any(check['name'] == 'Length Check' for check in report['checks']))

    def test_valid_description_passes_all_checks(self):
        """Test that a well-formed description passes all validation checks."""
        inputs = {
            "market_analysis_results": self.market_analysis,
            "title_final": self.final_title,
            "product_data": self.product_data
        }
        # The default generated description should be valid
        result = self.generator.execute(inputs, {}, None)
        report = result['validation_report']
        
        self.assertEqual(report['overall_status'], 'PASS')

    def test_description_with_forbidden_word_fails(self):
        """Test that a description with a forbidden term fails validation."""
        # Manually create a description with a forbidden word
        self.generator.rules['validation_rules']['forbidden_terms_always'] = ['free', 'plated']
        
        description = "This is a great ring with free shipping."
        report = self.generator._validate_description(description, self.market_analysis)

        self.assertEqual(report['overall_status'], 'FAIL')
        self.assertTrue(any(check['name'] == 'Forbidden Words Check' and check['status'] == 'FAIL' for check in report['checks']))

    def test_description_too_short_fails_length_check(self):
        """Test that a short description fails the length validation."""
        self.generator.rules['validation_rules']['description_min_chars'] = 500
        
        description = "Short description."
        report = self.generator._validate_description(description, self.market_analysis)

        self.assertEqual(report['overall_status'], 'FAIL')
        self.assertTrue(any(check['name'] == 'Length Check' and check['status'] == 'FAIL' for check in report['checks']))

    def test_missing_focus_keyword_in_hook_fails(self):
        """Test that a description missing the focus keyword in the hook fails validation."""
        description = "A sentence without the main keyword. " + "a" * 300 # to pass length check
        
        # This market analysis has "Handmade Gold Ring" as the primary focus keyword
        report = self.generator._validate_description(description, self.market_analysis)

        self.assertEqual(report['overall_status'], 'FAIL')
        self.assertTrue(any(check['name'] == 'Focus Keyword Check' and check['status'] == 'FAIL' for check in report['checks']))

    def test_handles_missing_inputs_gracefully(self):
        """Test that the execute method returns an error string if inputs are missing."""
        result = self.generator.execute({}, {}, None)
        self.assertIn("Error", result['description_final'])

    def test_all_logistics_information_is_included(self):
        """
        Verify that all mandatory logistics phrases from the advisory guide
        are included in the final description.
        """
        inputs = {
            "market_analysis_results": self.market_analysis,
            "title_final": self.final_title,
            "product_data": self.product_data
        }
        result = self.generator.execute(inputs, {}, None)
        description = result['description_final']
        
        # Get the required phrases from the loaded rules
        guide = self.generator.rules.get('structure_guide', {})
        must_includes = guide.get('must_include_from_product_info', [])
        
        self.assertGreater(len(must_includes), 0, "No logistics phrases found in the loaded rules to test against.")

        for item in must_includes:
            with self.subTest(item=item):
                self.assertIn(item, description, f"The required logistic info '{item}' was not found in the description.")

if __name__ == '__main__':
    unittest.main()
