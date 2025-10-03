import unittest
import json
from unittest.mock import MagicMock
from compliance_checker import ComplianceChecker
from version_control import VersionControl

class TestComplianceChecker(unittest.TestCase):

    def setUp(self):
        """Set up a mock context and checker for each test."""
        self.checker = ComplianceChecker()
        self.mock_knowledge_manager = MagicMock(spec=VersionControl)
        self.mock_knowledge_manager.reset_mock()
        self.mock_context = {
            "run": {
                "s": {
                    "14": {
                        "rs": {
                            "ruleset": [
                                {
                                    "id": "NO_BANNED_TERMS",
                                    "prm": {
                                        "list": ["forbidden", "bannedword"]
                                    }
                                },
                                {
                                    "id": "NO_ALLCAPS_SPAM",
                                    "prm": {}
                                },
                                {
                                    "id": "NO_MISLEADING_CLAIMS",
                                    "prm": {
                                        "claims": ["guaranteed", "100% effective"]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

    def test_pass_with_compliant_content(self):
        """Test that compliant content passes all checks."""
        inputs = {
            'title': 'A great product title',
            'description': 'This is a wonderful description.',
            'tags': ['good', 'quality']
        }
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(result['issues']), 0)
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()
        saved_data = self.mock_knowledge_manager.save_with_metadata.call_args[1]['data']
        self.assertEqual(saved_data['status'], 'PASS')

    def test_fail_with_banned_term(self):
        """Test that content with a banned term fails."""
        inputs = {
            'title': 'This title has a forbidden word',
            'description': 'Description is clean.',
            'tags': ['clean']
        }
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['rule_id'], 'NO_BANNED_TERMS')
        self.assertIn("'forbidden'", result['issues'][0]['message'])
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_fail_with_all_caps_spam(self):
        """Test that content with ALL CAPS words fails."""
        inputs = {
            'title': 'AMAZING SALE NOW',
            'description': 'This is an URGENT offer.',
            'tags': ['sale']
        }
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['rule_id'], 'NO_ALLCAPS_SPAM')
        message = result['issues'][0]['message']
        self.assertIn("AMAZING", message)
        self.assertIn("URGENT", message)
        self.assertIn("SALE", message)
        self.assertIn("NOW", message)
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_fail_with_misleading_claim(self):
        """Test that content with a misleading claim fails."""
        inputs = {
            'title': 'A good product',
            'description': 'This product is 100% effective and amazing.',
            'tags': ['effective']
        }
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['rule_id'], 'NO_MISLEADING_CLAIMS')
        self.assertIn("'100% effective'", result['issues'][0]['message'])
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_fail_with_multiple_issues(self):
        """Test that multiple issues are reported correctly."""
        inputs = {
            'title': 'This title is a SPECIAL OFFER',
            'description': 'It contains a forbidden word.',
            'tags': ['guaranteed']
        }
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 3)

        rule_ids = {issue['rule_id'] for issue in result['issues']}
        self.assertIn('NO_BANNED_TERMS', rule_ids)
        self.assertIn('NO_ALLCAPS_SPAM', rule_ids)
        self.assertIn('NO_MISLEADING_CLAIMS', rule_ids)
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_fail_with_missing_ruleset(self):
        """Test failure when the ruleset is missing from the context."""
        inputs = {'title': 'Any title', 'description': '', 'tags': []}
        empty_context = {}
        result = self.checker.execute(inputs, empty_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['rule_id'], 'LOAD_ERROR')
        self.assertIn('not found', result['issues'][0]['message'])
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_fail_with_malformed_ruleset(self):
        """Test failure when the ruleset in the context is not a list."""
        inputs = {'title': 'Any title', 'description': '', 'tags': []}
        malformed_context = {
            "run": {"s": {"14": {"rs": {"ruleset": "this is not a list"}}}}
        }
        result = self.checker.execute(inputs, malformed_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['rule_id'], 'LOAD_ERROR')
        self.assertIn('is not a list', result['issues'][0]['message'])
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

    def test_pass_with_empty_inputs(self):
        """Test that empty inputs do not cause an error and pass."""
        inputs = {'title': '', 'description': '', 'tags': []}
        result = self.checker.execute(inputs, self.mock_context, self.mock_knowledge_manager)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(result['issues']), 0)
        self.mock_knowledge_manager.save_with_metadata.assert_called_once()

if __name__ == '__main__':
    unittest.main()