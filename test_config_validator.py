import unittest
from unittest.mock import patch, mock_open
import os
import sys
import json
import logging

# Add project root to path to allow direct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from config_validator import ConfigValidator

# Suppress logging output during tests
logging.disable(logging.CRITICAL)

class TestConfigValidator(unittest.TestCase):

    def setUp(self):
        """Set up a new ConfigValidator instance for each test."""
        self.validator = ConfigValidator()
        self.valid_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            },
            "required": ["name"]
        }
        self.valid_config = {
            "fs": {
                "schema_v": {
                    "schema_ref": "internal://schemas/finalset"
                }
            },
            "_meta": {
                "schemas": {
                    "finalset": self.valid_schema
                }
            },
            "name": "test_config"
            # "value" is optional
        }
        self.invalid_config_missing_required = self.valid_config.copy()
        del self.invalid_config_missing_required["name"]

        self.invalid_config_wrong_type = self.valid_config.copy()
        self.invalid_config_wrong_type["name"] = 123 # Should be a string

    @patch("builtins.open")
    def test_validation_success(self, mock_file):
        """Test that a valid config file passes validation."""
        mock_file.return_value = mock_open(read_data=json.dumps(self.valid_config)).return_value
        result = self.validator.execute({"config_file_path": "dummy/path.json"}, {})
        self.assertEqual(result['status'], 'OK')

    @patch("builtins.open")
    def test_validation_fails_on_missing_required_field(self, mock_file):
        """Test that validation fails when a required field is missing."""
        from jsonschema.exceptions import ValidationError
        mock_file.return_value = mock_open(read_data=json.dumps(self.invalid_config_missing_required)).return_value
        with self.assertRaises(ValidationError) as cm:
            self.validator.execute({"config_file_path": "dummy/path.json"}, {})
        self.assertIn("'name' is a required property", str(cm.exception))

    @patch("builtins.open")
    def test_validation_fails_on_wrong_type(self, mock_file):
        """Test that validation fails when a field has the wrong type."""
        from jsonschema.exceptions import ValidationError
        mock_file.return_value = mock_open(read_data=json.dumps(self.invalid_config_wrong_type)).return_value
        with self.assertRaises(ValidationError) as cm:
            self.validator.execute({"config_file_path": "dummy/path.json"}, {})
        self.assertIn("123 is not of type 'string'", str(cm.exception))

    def test_get_schema_fails_with_bad_path(self):
        """Test that _get_schema raises an error if the schema path is invalid."""
        bad_config = {"fs": {"schema_v": {"schema_ref": "internal://non/existent/path"}}}
        with self.assertRaises(LookupError):
            self.validator._get_schema(bad_config)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_execute_fails_if_file_not_found(self, mock_file):
        """Test that execute raises an error if the config file doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.validator.execute({"config_file_path": "nonexistent/path.json"}, {})

if __name__ == '__main__':
    # Re-enable logging for manual runs
    logging.disable(logging.NOTSET)
    unittest.main()