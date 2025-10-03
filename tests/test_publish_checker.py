import unittest
import sys
import os
import shutil

# Add project_core to the Python path to allow importing PublishChecker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_core.publish_checker import PublishChecker

class TestPublishChecker(unittest.TestCase):

    def setUp(self):
        """Set up a base configuration and context for each test."""
        self.config = {}  # The checker doesn't use the config directly, but the orchestrator would pass it.
        self.checker = PublishChecker(config=self.config)

        # A base context that represents a successful state
        self.base_context = {
            "fs": {
                "ver": {
                    "pattern": "test_v{N}_{sha12}.json"
                }
            },
            'run': {
                's': {
                    '18': {
                        'rls': [
                            'CHECK_LISTING_STATUS',
                            'CHECK_EXPORT_ARTIFACTS',
                            'CHECK_COMPLIANCE_STATUS',
                            'CHECK_ADS_SYNC_STATUS',
                            'CHECK_MEDIA_MANIFEST'
                        ]
                    }
                }
            },
            'listing': {
                'status': 'PASS',
                'final': {
                    'media': {
                        'manifest': [{'type': 'studio', 'url': 'image.jpg'}]
                    }
                }
            },
            'export': {
                'file_path': 'output/export.csv',
                'sha256': 'a1b2c3d4e5f6'
            },
            'compliance': {'status': 'PASS'},
            'ads_sync': {'status': 'PASS'}
        }

    def tearDown(self):
        """Clean up the outputs directory created by VersionControl."""
        if os.path.exists("outputs"):
            shutil.rmtree("outputs")

    def test_execute_ready_status(self):
        """Test the ideal case where all checks pass and status is READY."""
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'READY')
        self.assertEqual(len(result['checklist_results']), 5)
        self.assertTrue(all(r['status'] == 'PASS' for r in result['checklist_results']))
        self.assertEqual(result['notes'], '')

    def test_execute_blocked_by_listing_status(self):
        """Test that the status is BLOCKED if listing status is not PASS."""
        self.base_context['listing']['status'] = 'FAIL'
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Listing assembly status is 'FAIL'", result['notes'])

    def test_execute_blocked_by_missing_export_path(self):
        """Test that the status is BLOCKED if the export file path is missing."""
        self.base_context['export']['file_path'] = None
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Export artifacts are incomplete", result['notes'])

    def test_execute_blocked_by_missing_export_sha(self):
        """Test that the status is BLOCKED if the export SHA256 is missing."""
        self.base_context['export']['sha256'] = ''
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Export artifacts are incomplete", result['notes'])

    def test_execute_blocked_by_compliance_status(self):
        """Test that the status is BLOCKED if compliance status is not PASS."""
        self.base_context['compliance']['status'] = 'FAIL'
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Compliance status is 'FAIL'", result['notes'])

    def test_execute_blocked_by_ads_sync_status(self):
        """Test that the status is BLOCKED if ads_sync status is FAIL."""
        self.base_context['ads_sync']['status'] = 'FAIL'
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Ads sync status is 'FAIL'", result['notes'])

    def test_execute_ready_with_ads_sync_warn(self):
        """Test that the status is READY even if ads_sync status is WARN."""
        self.base_context['ads_sync']['status'] = 'WARN'
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'READY')
        self.assertEqual(result['notes'], '')

    def test_execute_blocked_by_empty_media_manifest(self):
        """Test that the status is BLOCKED if the media manifest is empty."""
        self.base_context['listing']['final']['media']['manifest'] = []
        result = self.checker.execute(inputs={}, context=self.base_context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Final media check failed", result['notes'])

    def test_execute_blocked_by_missing_rules(self):
        """Test for a configuration error if the rules are not in the context."""
        context = {} # Empty context
        result = self.checker.execute(inputs={}, context=context)
        self.assertEqual(result['publish_status'], 'BLOCKED')
        self.assertIn("Configuration error: Could not load checklist rules", result['notes'])

if __name__ == '__main__':
    unittest.main()