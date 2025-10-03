import unittest
import os
import json
import hashlib
import shutil
from unittest.mock import patch, MagicMock

# Since version_control is not in a package, and we are running from the root,
# we need to adjust the python path to import it.
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from version_control import VersionControl

class TestVersionControl(unittest.TestCase):

    def setUp(self):
        """Set up a test environment."""
        self.test_output_dir = "test_outputs"

        # Clean up previous test runs
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

        # Mock configuration from finalv1.json
        self.mock_config = {
            "pattern": "TEST__{sha12}_v{N}.json",
            "diff_j": {
                "pattern": "PATCH_TEST_%Y%m%d_%H%M%S.diff.json"
            }
        }

        # Instantiate the class
        self.vc = VersionControl(self.mock_config)

        # Override the directory paths to point to our test directory
        self.vc.base_dir = os.path.join(self.test_output_dir, "fs")
        self.vc.ver_dir = os.path.join(self.vc.base_dir, "ver")
        self.vc.diff_dir = os.path.join(self.vc.base_dir, "diff_j")

        # Ensure these test directories exist
        os.makedirs(self.vc.ver_dir, exist_ok=True)
        os.makedirs(self.vc.diff_dir, exist_ok=True)


    def tearDown(self):
        """Clean up the test environment."""
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_initialization(self):
        """Test if the class initializes correctly."""
        self.assertEqual(self.vc.pattern, self.mock_config["pattern"])
        self.assertTrue(os.path.exists(self.vc.ver_dir))

    def test_save_new_version_atomic_write(self):
        """Test the atomic write functionality of save_new_version."""
        base_path = "test_data/my_file.json"
        data = {"key": "value", "id": 1}

        result = self.vc.save_new_version(base_path, data)

        # 1. Check if the file exists at the returned path
        self.assertTrue(os.path.exists(result["filepath"]))

        # 2. Check if the content is correct
        with open(result["filepath"], 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(data, saved_data)

        # 3. Check the returned dictionary structure
        self.assertIn("filepath", result)
        self.assertIn("version", result)
        self.assertIn("sha256", result)
        self.assertEqual(result["version"], 1)

    def test_sha256_hash_calculation(self):
        """Test if the SHA256 hash is calculated correctly."""
        base_path = "test_data/my_file.json"
        data = {"key": "value", "id": 1}

        # Manually calculate expected hash
        serialized_data = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8')
        expected_hash = hashlib.sha256(serialized_data).hexdigest()

        result = self.vc.save_new_version(base_path, data)
        self.assertEqual(result["sha256"], expected_hash)

        # Verify the hash in the filename (first 12 chars)
        self.assertIn(expected_hash[:12], os.path.basename(result["filepath"]))

    def test_version_increment(self):
        """Test if the version number increments correctly."""
        base_path = "test_data/my_file.json"
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}

        result1 = self.vc.save_new_version(base_path, data1)
        self.assertEqual(result1["version"], 1)

        result2 = self.vc.save_new_version(base_path, data2)
        self.assertEqual(result2["version"], 2)

    def test_save_with_metadata(self):
        """Test the save_with_metadata function."""
        base_path = "metadata_test/my_data.json"
        data = {"field": "some_data"}
        actor = "test_script.py"
        reason = "Unit test execution."

        save_result = self.vc.save_with_metadata(base_path, data, actor, reason)

        # Check if the data file was created
        self.assertTrue(os.path.exists(save_result["filepath"]))

        # Check if the metadata file was created
        meta_filepath = os.path.splitext(save_result["filepath"])[0] + ".meta.json"
        self.assertTrue(os.path.exists(meta_filepath))

        # Verify metadata content
        with open(meta_filepath, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        self.assertEqual(metadata["actor"], actor)
        self.assertEqual(metadata["reason"], reason)
        self.assertEqual(metadata["version"], save_result["version"])
        self.assertEqual(metadata["sha256"], save_result["sha256"])
        self.assertEqual(metadata["source_file"], save_result["filepath"])
        self.assertIn("timestamp", metadata)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)