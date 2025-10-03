import unittest
import os
import json
import glob
from listing_assembler import ListingAssembler
from version_control import VersionControl

class TestRefactoredListingAssembler(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.assembler = ListingAssembler()
        self.test_output_dir = 'outputs/fs/ver'
        os.makedirs(self.test_output_dir, exist_ok=True)
        # Clean up previous test runs
        self._cleanup_files()

    def tearDown(self):
        """Clean up files created during tests."""
        self._cleanup_files()

    def _cleanup_files(self):
        """More robust helper to remove any test-generated files."""
        if not os.path.exists(self.test_output_dir):
            return
        print(f"--- Cleaning up directory: {self.test_output_dir} ---")
        for filename in os.listdir(self.test_output_dir):
            if "assembled_listing" in filename:
                filepath = os.path.join(self.test_output_dir, filename)
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except OSError as e:
                    print(f"Error removing file {filepath}: {e}")
        print("--- Cleanup complete ---")

    def test_execute_saves_versioned_json_with_metadata(self):
        """
        Verify that execute() correctly assembles data and saves it as a versioned
        JSON file with correct metadata.
        """
        # 1. Setup
        context = {
            'product_data': {'data': {'id': 'prod-123', 'products': [{'pricing': {'price': '99.99', 'currency': 'USD'}}]}},
            'final_title_output': {'title_final': 'Refactored Test Title'},
            'final_description_output': {'description': 'A great refactored product.'},
            'final_tags_output': {'tags': ['refactor', 'test', 'python']},
            'compliance_report': {'status': 'PASS'}
        }

        # 2. Execute
        result = self.assembler.execute(inputs={}, context=context)

        # 3. Assert execution status
        self.assertEqual(result['status'], 'PASS', f"Execution failed with message: {result.get('message')}")
        self.assertIn('Listing assembled and saved successfully', result['message'])

        # 4. Find and verify the created files
        all_files = glob.glob(os.path.join(self.test_output_dir, 'assembled_listing_*.json'))

        # Correctly separate the data file from the metadata file
        json_files = [f for f in all_files if not f.endswith('.meta.json')]
        meta_files = [f for f in all_files if f.endswith('.meta.json')]

        self.assertEqual(len(json_files), 1, "Expected one JSON data file to be created.")
        self.assertEqual(len(meta_files), 1, "Expected one metadata file to be created.")

        json_filepath = json_files[0]
        meta_filepath = meta_files[0]

        # 5. Verify JSON content
        with open(json_filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data['record_id'], 'prod-123')
        self.assertEqual(saved_data['product.title'], 'Refactored Test Title')
        self.assertEqual(saved_data['product.tags'], 'refactor,test,python')

        # 6. Verify Metadata content
        with open(meta_filepath, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        self.assertEqual(meta_data['actor'], 'listing_assembler.py')
        self.assertEqual(meta_data['reason'], 'Assembled final listing from all SEO components.')
        self.assertIn(os.path.basename(json_filepath), meta_data['source_file'])
