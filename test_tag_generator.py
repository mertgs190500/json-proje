import unittest
from unittest.mock import MagicMock, patch
import os
import json

# Add project root to path to allow direct imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from tag_generator import TagGenerator
from version_control import VersionControl

class TestTagGenerator(unittest.TestCase):

    def setUp(self):
        """Set up a new TagGenerator instance for each test."""
        self.tag_generator = TagGenerator()

        # Mock configuration for VersionControl
        self.mock_vc_config = {
            "pattern": "test_v{N}_{sha12}.json",
            "base_dir": "outputs/fs",
            "ver_dir": "outputs/fs/ver"
        }

        # Clean up created directories after tests
        self.addCleanup(self.cleanup_files)

    def cleanup_files(self):
        """Remove files and directories created during tests."""
        test_output_dir = "outputs"
        if os.path.exists(test_output_dir):
            import shutil
            # shutil.rmtree(test_output_dir) # To be safe, let's just remove the specific files.
            ver_dir = os.path.join(test_output_dir, "fs", "ver")
            if os.path.exists(ver_dir):
                for f in os.listdir(ver_dir):
                    if f.startswith("generated_tags_"):
                        os.remove(os.path.join(ver_dir, f))


    def test_execute_generates_tags_and_saves(self):
        """
        Test that the execute method generates tags and calls the save function
        with the correct parameters.
        """
        # --- Arrange ---
        # 1. Mock inputs for the tag generator
        inputs = {
            'market_analysis': {
                'popular_keywords_top': ['handmade jewelry', 'silver necklace'],
                'competitor_signals': {'main_themes': ['boho style', 'minimalist design']},
                'market_snapshot': {'keyword_gaps': ['custom engraving']}
            },
            'keyword_data': {
                'focus_keywords': ['personalized gift', 'unique necklace'],
                'supporting_keywords': ['artisan crafted', 'everyday wear']
            },
            'title_data': {'final_title': 'Handmade Silver Necklace - Personalized Gift'},
            'description_data': {'final_description': 'A unique necklace, perfect for everyday wear. Artisan crafted boho style.'},
            'product_attributes': {'material': 'silver'}
        }
        context = {} # Not used by tag_generator

        # 2. Mock VersionControl
        # We use a real VC instance to ensure it works, but we can also mock save_with_metadata if we only want to check the call
        mock_knowledge_manager = VersionControl(self.mock_vc_config)
        mock_knowledge_manager.save_with_metadata = MagicMock()

        # --- Act ---
        result = self.tag_generator.execute(inputs, context, knowledge_manager=mock_knowledge_manager)

        # --- Assert ---
        # 1. Assert the output is correct
        self.assertIn('final_tags', result)
        self.assertIsInstance(result['final_tags'], list)
        self.assertTrue(len(result['final_tags']) > 0)
        self.assertIn('personalized gift', result['final_tags']) # Check for a high-priority generated tag

        # 2. Assert that save_with_metadata was called once
        mock_knowledge_manager.save_with_metadata.assert_called_once()

        # 3. Assert the call arguments
        call_args = mock_knowledge_manager.save_with_metadata.call_args[1] # Get kwargs
        self.assertEqual(call_args['base_path'], 'outputs/generated_tags.json')
        self.assertEqual(call_args['actor'], 'tag_generator.py')
        self.assertEqual(call_args['reason'], 'Generated 13 SEO tags based on analysis.')
        self.assertEqual(call_args['data'], result) # The data saved should be the entire result dict

    def test_no_tags_generated_if_pool_is_empty(self):
        """Test that an empty list is returned if no candidate tags can be generated."""
        # --- Arrange ---
        inputs = {} # Empty inputs
        context = {}
        mock_knowledge_manager = MagicMock(spec=VersionControl)

        # --- Act ---
        result = self.tag_generator.execute(inputs, context, knowledge_manager=mock_knowledge_manager)

        # --- Assert ---
        self.assertEqual(result, {"final_tags": []})
        mock_knowledge_manager.save_with_metadata.assert_not_called() # Should not save if no tags are generated


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)