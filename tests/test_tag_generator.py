import unittest
import os
import json
from unittest.mock import MagicMock, patch
from tag_generator import TagGenerator

class TestTagGenerator(unittest.TestCase):

    def setUp(self):
        """Set up a new TagGenerator instance for each test."""
        self.tag_generator = TagGenerator()

    def test_competitor_gap_analysis_integration(self):
        """
        Test that competitor tags are correctly identified as gaps and prioritized.
        """
        # Mock inputs
        inputs = {
            'market_analysis': {
                'popular_keywords_top': ['gold ring', '14k gold'],
                'competitor_signals': {'main_themes': ['handmade jewelry']},
                'market_snapshot': {'keyword_gaps': []}
            },
            'keyword_data': {
                'focus_keywords': ['solid gold ring'],
                'supporting_keywords': ['minimalist ring']
            },
            'title_data': {'final_title': 'Solid Gold Ring for Women'},
            'description_data': {'final_description': 'A beautiful handmade solid gold ring.'},
            'product_attributes': {'material': 'gold'},
            'competitor_tags_data': {
                'data': [
                    {'Tags': 'gold ring, engagement ring, wedding band'},
                    {'Tags': '14k gold, promise ring, anniversary gift'}
                ]
            }
        }

        # Our tags: 'gold ring', '14k gold', 'handmade jewelry', 'solid gold ring', 'minimalist ring', 'women'
        # Competitor tags: 'gold ring', 'engagement ring', 'wedding band', '14k gold', 'promise ring', 'anniversary gift'
        # Opportunity tags (gaps): 'engagement ring', 'wedding band', 'promise ring', 'anniversary gift'

        # Mock the knowledge_manager's save_with_metadata method
        mock_knowledge_manager = MagicMock()

        # Execute the generator
        result = self.tag_generator.execute(inputs, context={}, knowledge_manager=mock_knowledge_manager)
        final_tags = result.get('final_tags', [])

        # Assert that save_with_metadata was not called, as we passed a generic MagicMock
        # A more specific mock could assert it *was* called, but we just want to prevent file writes.
        mock_knowledge_manager.save_with_metadata.assert_not_called()

        # Assertions
        self.assertIn('engagement ring', final_tags)
        self.assertIn('wedding band', final_tags)
        self.assertIn('promise ring', final_tags)
        self.assertIn('anniversary gift', final_tags)

        # Check that some of our original high-priority tags are still present
        self.assertTrue(any(tag in final_tags for tag in ['solid gold ring', 'minimalist ring']))
        self.assertEqual(len(final_tags), 13)

    def test_empty_inputs(self):
        """Test that the generator handles empty inputs gracefully."""
        inputs = {
            'market_analysis': {},
            'keyword_data': {},
            'title_data': {},
            'description_data': {},
            'product_attributes': {},
            'competitor_tags_data': {}
        }
        result = self.tag_generator.execute(inputs, context={}, knowledge_manager=None)
        self.assertEqual(result['final_tags'], [])

if __name__ == '__main__':
    unittest.main()