import unittest
import os
import csv
from datetime import datetime
from exporter import Exporter

class TestExporter(unittest.TestCase):

    def setUp(self):
        self.config = {
            "exp": {
                "cols": [
                    "record_id", "product.title", "product.tags"
                ],
                "naming": {
                    "pattern": "TEST_EXPORT_%Y%m%d_%H%M%S_v{N}.csv"
                }
            }
        }
        self.exporter = Exporter(self.config)
        self.output_dir = 'output/fs/export'
        # Clean up any previous test files
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.startswith("TEST_EXPORT"):
                    os.remove(os.path.join(self.output_dir, f))

    def tearDown(self):
        # Clean up files created during tests
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.startswith("TEST_EXPORT"):
                    os.remove(os.path.join(self.output_dir, f))

    def test_execute_success(self):
        inputs = {
            'assembled_listing': {
                'record_id': '123',
                'product.title': 'My Test Product',
                'product.tags': 'test,product',
                'extra_field': 'should_not_be_exported'
            }
        }
        context = {}

        result = self.exporter.execute(inputs, context)

        self.assertEqual(result['status'], 'PASS')
        self.assertIn('Listing exported successfully', result['message'])

        filepath = result['data']['filepath']
        self.assertTrue(os.path.exists(filepath))

        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            self.assertEqual(header, self.config['exp']['cols'])

            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0], ['123', 'My Test Product', 'test,product'])

    def test_execute_no_input(self):
        inputs = {'assembled_listing': None}
        context = {}

        result = self.exporter.execute(inputs, context)

        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('No assembled listing provided', result['message'])

    def test_column_order_and_completeness(self):
        inputs = {
            'assembled_listing': {
                'product.tags': 'b,a',
                'record_id': '456',
                'product.title': 'Title First'
            }
        }
        context = {}

        result = self.exporter.execute(inputs, context)
        self.assertEqual(result['status'], 'PASS')
        filepath = result['data']['filepath']

        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            self.assertEqual(reader.fieldnames, self.config['exp']['cols'])

            row = next(reader)
            self.assertEqual(row['record_id'], '456')
            self.assertEqual(row['product.title'], 'Title First')
            self.assertEqual(row['product.tags'], 'b,a')

if __name__ == '__main__':
    unittest.main()