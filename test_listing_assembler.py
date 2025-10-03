import unittest
import json
from listing_assembler import ListingAssembler

class TestListingAssembler(unittest.TestCase):

    def setUp(self):
        self.config = {
            "exp": {
                "cols": [
                    "record_id", "op_type", "is_deleted", "product.title",
                    "product.description", "product.tags", "pricing.price_value",
                    "pricing.price_currency", "image_1", "image_2", "image_3",
                    "image_4", "image_5"
                ]
            }
        }
        self.assembler = ListingAssembler(self.config)

    def test_execute_success(self):
        inputs = {}
        context = {
            'compliance_report': {'status': 'PASS'},
            'product_data': {'id': '12345', 'pricing': {'price': '100.00', 'currency': 'USD'}},
            'title': 'Test Title',
            'description': 'Test Description',
            'tags': ['tag1', 'tag2'],
            'images': ['img1.jpg', 'img2.jpg']
        }

        result = self.assembler.execute(inputs, context)

        self.assertEqual(result['status'], 'PASS')
        self.assertIn('Listing assembled successfully', result['message'])

        data = result['data']
        self.assertIsNotNone(data)
        self.assertEqual(data['record_id'], '12345')
        self.assertEqual(data['product.title'], 'Test Title')
        self.assertEqual(data['product.tags'], 'tag1,tag2')
        self.assertEqual(data['pricing.price_value'], '100.00')
        self.assertEqual(data['image_1'], 'img1.jpg')
        self.assertEqual(data['image_3'], '')

    def test_execute_compliance_fail(self):
        inputs = {}
        context = {
            'compliance_report': {'status': 'FAIL'}
        }

        result = self.assembler.execute(inputs, context)

        self.assertEqual(result['status'], 'FAIL')
        self.assertIn('Compliance check did not pass', result['message'])
        self.assertIsNone(result['data'])

    def test_column_completeness(self):
        inputs = {}
        context = {
            'compliance_report': {'status': 'PASS'},
            'product_data': {'id': '67890'},
            'title': 'Another Title'
        }

        result = self.assembler.execute(inputs, context)

        self.assertEqual(result['status'], 'PASS')
        data = result['data']

        for col in self.config['exp']['cols']:
            self.assertIn(col, data)
            self.assertIsNotNone(data[col])

if __name__ == '__main__':
    unittest.main()