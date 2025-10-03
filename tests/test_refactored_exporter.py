import unittest
import os
import json
import glob
import csv
from exporter import Exporter
from version_control import VersionControl

class TestRefactoredExporter(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.exporter = Exporter()
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
        # This ensures all related artifacts are removed, regardless of extension
        for filename in os.listdir(self.test_output_dir):
            if "etsy_listing_export" in filename:
                filepath = os.path.join(self.test_output_dir, filename)
                try:
                    os.remove(filepath)
                except OSError as e:
                    print(f"Error removing file {filepath}: {e}")

    def test_execute_saves_versioned_csv_with_metadata(self):
        """
        Verify that execute() correctly exports data to a versioned
        CSV file with correct metadata.
        """
        # 1. Setup
        inputs = {
            'assembled_listing': {
                'record_id': 'exp-456',
                'op_type': 'CREATE',
                'is_deleted': 'false',
                'product.title': 'Refactored CSV Export Test',
                'product.description': 'Description for export.',
                'product.tags': 'csv,export,refactor',
                'pricing.price_value': '199.99',
                'pricing.price_currency': 'CAD',
                'image_1': 'export_img1.jpg',
                'image_2': '',
                'image_3': '',
                'image_4': '',
                'image_5': ''
            }
        }

        # 2. Execute
        result = self.exporter.execute(inputs=inputs, context={})

        # 3. Assert execution status
        self.assertEqual(result['status'], 'PASS', f"Execution failed with message: {result.get('message')}")
        self.assertIn('Listing exported successfully', result['message'])

        # 4. Find and verify the created files
        # Find all files related to the export, then filter them
        all_files = glob.glob(os.path.join(self.test_output_dir, 'etsy_listing_export_*'))

        csv_files = [f for f in all_files if f.endswith('.csv')]
        meta_files = [f for f in all_files if f.endswith('.meta.json')]

        self.assertEqual(len(csv_files), 1, "Expected one CSV data file to be created.")
        self.assertEqual(len(meta_files), 1, "Expected one metadata file to be created.")

        csv_filepath = csv_files[0]
        meta_filepath = meta_files[0]

        # 5. Verify CSV content
        with open(csv_filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['record_id'], 'exp-456')
            self.assertEqual(row['product.title'], 'Refactored CSV Export Test')
            self.assertEqual(row['product.tags'], 'csv,export,refactor')

        # 6. Verify Metadata content
        with open(meta_filepath, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
        self.assertEqual(meta_data['actor'], 'exporter.py')
        self.assertEqual(meta_data['reason'], 'Exported final listing to CSV format for upload.')
        self.assertIn(os.path.basename(csv_filepath), meta_data['source_file'])
