import os
import logging
import json
import re
import hashlib
from datetime import datetime
from jsondiff import diff as jsondiff

class VersionControl:
    """
    Manages file versioning and diffing according to specified policies.
    Implements the "never overwrite, create a new version" principle.
    """

    def __init__(self, versioning_policy=None):
        """
        Initializes the version controller. The policy is now hardcoded
        to match the requirements from finalv1.json.
        """
        # Hardcoded patterns based on the task description
        self.ver_pattern = "FINALSET__{timestamp}__v{version}__{sha}.json"
        self.diff_pattern = "PATCH_{timestamp}.diff.json"
        self.ver_dir = "output/fs/ver"
        self.diff_dir = "output/fs/diff_j"

        # Ensure output directories exist
        os.makedirs(self.ver_dir, exist_ok=True)
        os.makedirs(self.diff_dir, exist_ok=True)

        logging.info(f"Version Control initialized. Versioning dir: '{self.ver_dir}', Diff dir: '{self.diff_dir}'")

    def _get_next_version(self):
        """
        Finds the next available version number by scanning the versioning directory.

        Returns:
            int: The next integer version number to be used.
        """
        # Regex to find version numbers in filenames like:
        # FINALSET__20251002_2048__v1__a1b2c3d4e5f6.json
        version_regex = re.compile(r"^FINALSET__\d{8}_\d{4}__v(\d+)__[a-f0-9]{12}\.json$")

        max_version = 0
        try:
            for f in os.listdir(self.ver_dir):
                match = version_regex.match(f)
                if match:
                    version = int(match.group(1))
                    if version > max_version:
                        max_version = version
        except FileNotFoundError:
            # This can happen if the ver_dir hasn't been created yet, which is fine.
            pass

        return max_version + 1

    def save_new_version(self, base_path_ignored, data):
        """
        Saves data to a new, versioned file according to the specified format.

        Args:
            base_path_ignored (str): This parameter is kept for API compatibility but is ignored
                                     as the output directory and filename format are now fixed.
            data (dict): The dictionary data to be saved as JSON.

        Returns:
            str: The full path of the newly created versioned file, or None on failure.
        """
        try:
            if not isinstance(data, dict):
                raise TypeError("Input 'data' must be a dictionary for hashing and JSON serialization.")

            # Get the next version number
            next_version = self._get_next_version()

            # Prepare data for hashing by creating a consistent string representation
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            data_bytes = data_str.encode('utf-8')

            # Calculate SHA-1 hash and truncate to the first 12 characters
            sha1_hash = hashlib.sha1(data_bytes).hexdigest()
            sha12 = sha1_hash[:12]

            # Get current timestamp formatted as required
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M")

            # Construct the new filename from the pattern
            new_filename = self.ver_pattern.format(
                timestamp=timestamp,
                version=next_version,
                sha=sha12
            )
            new_filepath = os.path.join(self.ver_dir, new_filename)

            logging.info(f"Saving new version: '{new_filepath}'")

            # Save the data to the new file
            with open(new_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return new_filepath
        except Exception as e:
            logging.error(f"Failed to save new version. Error: {e}")
            return None

    def diff_versions(self, file_v1_path, file_v2_path):
        """
        Generates a diff between two JSON files using the 'jsondiff' library and saves it
        to a new file with a timestamped name.

        Args:
            file_v1_path (str): Path to the first (older) JSON file.
            file_v2_path (str): Path to the second (newer) JSON file.

        Returns:
            str: The path to the saved diff file, or None on failure.
        """
        try:
            logging.info(f"Generating diff between '{file_v1_path}' and '{file_v2_path}'.")

            with open(file_v1_path, 'r', encoding='utf-8') as f1:
                data1 = json.load(f1)
            with open(file_v2_path, 'r', encoding='utf-8') as f2:
                data2 = json.load(f2)

            # Calculate the difference. Using dump=True returns a JSON-serializable string.
            diff_result_str = jsondiff(data1, data2, syntax='explicit', dump=True)

            # Create a precise timestamp for the patch file, including seconds
            patch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Construct the diff filename from the pattern
            diff_filename = self.diff_pattern.format(timestamp=patch_timestamp)
            diff_filepath = os.path.join(self.diff_dir, diff_filename)

            logging.info(f"Saving diff report to '{diff_filepath}'")

            # To save a formatted file, parse the string back into a Python object,
            # then dump it to the file with indentation.
            diff_obj = json.loads(diff_result_str)
            with open(diff_filepath, 'w', encoding='utf-8') as f:
                json.dump(diff_obj, f, indent=2, ensure_ascii=False)

            return diff_filepath
        except Exception as e:
            logging.error(f"Failed to create or save diff. Error: {e}")
            return None