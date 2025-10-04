import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import logging
import importlib

# Add project root to path to allow direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from system_health_checker import SystemHealthChecker

# Suppress logging output during tests
logging.disable(logging.CRITICAL)

class TestSystemHealthChecker(unittest.TestCase):

    def setUp(self):
        """Set up a new SystemHealthChecker instance for each test."""
        self.checker = SystemHealthChecker()

    @patch('importlib.metadata.version')
    def test_dependency_check_success(self, mock_version):
        """Test that dependency check passes with correct versions."""
        mock_version.side_effect = ['2.1.0', '4.2.0']
        required = {'pandas': '2.0.0', 'jsonschema': '4.0.0'}
        warnings = self.checker._check_dependencies(required)
        self.assertEqual(len(warnings), 0)

    @patch('importlib.metadata.version')
    def test_dependency_check_outdated(self, mock_version):
        """Test that dependency check warns for outdated versions."""
        mock_version.side_effect = ['1.5.0']
        required = {'pandas': '2.0.0'}
        warnings = self.checker._check_dependencies(required)
        self.assertEqual(len(warnings), 1)
        self.assertIn("daha eski", warnings[0])

    @patch('importlib.metadata.version')
    def test_dependency_check_not_found(self, mock_version):
        """Test that dependency check warns for missing packages."""
        # Configure the mock to raise PackageNotFoundError for a specific package
        mock_version.side_effect = importlib.metadata.PackageNotFoundError
        required = {'nonexistent_package': '1.0.0'}
        warnings = self.checker._check_dependencies(required)
        self.assertEqual(len(warnings), 1)
        self.assertIn("bulunamadı", warnings[0])

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('system_health_checker.genai')
    def test_api_check_success(self, mock_genai):
        """Test that API health check passes when API is accessible."""
        mock_genai.list_models.return_value = True
        self.assertTrue(self.checker._check_api_accessibility())

    @patch.dict(os.environ, {}, clear=True)
    def test_api_check_no_key(self):
        """Test that API health check fails if API key is not set."""
        with self.assertRaises(ValueError) as cm:
            self.checker._check_api_accessibility()
        self.assertIn("ortam değişkeni ayarlanmamış", str(cm.exception))

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('system_health_checker.genai')
    def test_api_check_connection_error(self, mock_genai):
        """Test that API health check fails on connection errors."""
        mock_genai.list_models.side_effect = Exception("Network error")
        with self.assertRaises(ConnectionError) as cm:
            self.checker._check_api_accessibility()
        self.assertIn("erişilemiyor", str(cm.exception))

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('system_health_checker.genai', None)
    def test_api_check_no_library(self):
        """Test that API check fails if the google-generativeai library is not installed."""
        # To properly test this, we need to reload the module with genai as None
        # This is complex in a running test, so we'll simulate the check directly.
        # The check inside the method handles `genai is None`
        with self.assertRaises(ImportError) as cm:
             self.checker._check_api_accessibility()
        self.assertIn("yüklü değil", str(cm.exception))


if __name__ == '__main__':
    # Re-enable logging for manual runs
    logging.disable(logging.NOTSET)
    unittest.main()