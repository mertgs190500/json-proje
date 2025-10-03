import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from csv_ingestor import CsvIngestor

class TestCsvIngestor(unittest.TestCase):

    @patch('csv_ingestor.VersionControl')
    @patch('csv_ingestor.load_json')
    def test_execute_saves_versioned_csv_and_returns_data(self, mock_load_json, mock_version_control):
        # --- Setup Mocks ---
        # Mock for load_json to return a fake config
        mock_load_json.return_value = {
            "fs": {
                "ver": {
                    "pattern": "test_v{N}_{sha12}.csv"
                }
            }
        }

        # Mock for the VersionControl instance and its save_new_version method
        mock_vc_instance = MagicMock()
        mock_vc_instance.save_new_version.return_value = {"filepath": "runtime/csv/test_file_clean_v1_abc123.csv"}
        mock_version_control.return_value = mock_vc_instance

        # --- Test Data ---
        ingestor = CsvIngestor()

        # Sample raw CSV data with extra quotes and whitespace in headers
        raw_csv_content = b"'Header 1' , \"Header 2\"\nvalue1,value2\n"

        inputs = {
            "raw_content": raw_csv_content,
            "file_path": "source_data/test_file.csv",
            "resolved_profile": {
                "encoding": ["utf-8"],
                "delimiter_probe": [","],
                "description": "Test Profile"
            }
        }

        # --- Execute ---
        result = ingestor.execute(inputs=inputs, context={})

        # --- Assertions ---

        # 1. Check if VersionControl was initialized correctly
        mock_load_json.assert_called_once_with('project_core/finalv1.json')
        mock_version_control.assert_called_once_with(versioning_config={'pattern': 'test_v{N}_{sha12}.csv'})

        # 2. Check if save_new_version was called correctly
        mock_vc_instance.save_new_version.assert_called_once()

        # 3. Verify the arguments passed to save_new_version
        call_args = mock_vc_instance.save_new_version.call_args
        base_path_arg = call_args[1]['base_path']
        data_arg = call_args[1]['data']

        self.assertEqual(base_path_arg, "runtime/csv/test_file_clean.csv")

        # Expected CSV string after header cleaning
        expected_csv_data = "Header 1,Header 2\nvalue1,value2\n"
        self.assertEqual(data_arg, expected_csv_data)

        # 4. Verify the orchestrator return contract is maintained
        self.assertEqual(result["status"], "success")
        self.assertIsInstance(result["data"], list)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0], {"Header 1": "value1", "Header 2": "value2"})

if __name__ == '__main__':
    unittest.main()