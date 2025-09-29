import unittest
import os
import json
import uretim_scripti

class TestGuvenlik(unittest.TestCase):

    def setUp(self):
        """Set up test environment."""
        self.test_state_path = "test_state.json"
        self.initial_data = {"key": "value", "initial": True, "long_string": "a" * 100}

        # Define the configuration directly in the test
        self.config = {
            "pl": {
                "security": {
                    "size_shrink_guard": {
                        "threshold_bytes": 1,  # Trigger on any shrink
                        "threshold_percent": 0.001, # Trigger on any shrink
                        "on_violation": "block_and_request_approval"
                    }
                }
            },
            "fs": {
                "rt_p": {
                    "run_state_file": self.test_state_path
                }
            }
        }

        # Create an initial state file with some data
        initial_state = {
            "last_completed_step_id": "init",
            "uretim_verileri": self.initial_data
        }
        with open(self.test_state_path, 'w') as f:
            json.dump(initial_state, f)

    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.test_state_path):
            os.remove(self.test_state_path)

    def test_size_shrink_guard_pass(self):
        """Test that the size shrink guard passes when the new data is larger."""
        new_data = {"key": "value", "initial": True, "long_string": "a" * 200} # Larger data

        # This should pass and return True
        result = uretim_scripti.durum_yonetimi(self.config, 'test_pass_step', new_data, 'yaz')
        self.assertTrue(result)

        # Verify the new data was written
        with open(self.test_state_path, 'r') as f:
            written_data = json.load(f)
        self.assertEqual(written_data['uretim_verileri'], new_data)

    def test_size_shrink_guard_fail_and_block(self):
        """Test that the size shrink guard fails and blocks the write."""
        new_data = {}  # Significantly smaller data

        # This should return False because the size shrink guard blocks it
        result = uretim_scripti.durum_yonetimi(self.config, 'test_fail_step', new_data, 'yaz')
        self.assertFalse(result)

        # Verify the original data was not overwritten
        with open(self.test_state_path, 'r') as f:
            state = json.load(f)
        self.assertEqual(state['uretim_verileri'], self.initial_data)

if __name__ == '__main__':
    unittest.main()