import os
import logging
import json
import re

class VersionControl:
    """
    Manages file versioning to prevent overwriting and ensure data integrity.
    Implements the "never overwrite, create a new version" principle.
    """

    def __init__(self, versioning_policy=None):
        """
        Initializes the version controller with a versioning policy.

        Args:
            versioning_policy (dict): A dictionary defining the versioning pattern, e.g.,
                                      {'pattern': '_v{version}'}.
        """
        if versioning_policy is None:
            versioning_policy = {}
        # Default pattern: filename_v1.json, filename_v2.json, etc.
        self.pattern = versioning_policy.get("pattern", "_v{version}")
        logging.info(f"Version Control initialized with pattern: '{self.pattern}'")

    def _get_next_version(self, base_path):
        """
        Finds the next available version number for a given base path.

        Args:
            base_path (str): The base file path (e.g., 'data/listing.json').

        Returns:
            int: The next integer version number to be used.
        """
        directory, filename = os.path.split(base_path)
        base_name, ext = os.path.splitext(filename)

        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Regex to find existing versioned files
        # It looks for the base name, the start of the version pattern (e.g., '_v'), a number, and the extension.
        pattern_regex_part = self.pattern.format(version="(\d+)").replace("{", "\\{").replace("}", "\\}")
        version_regex = re.compile(f"^{re.escape(base_name)}{pattern_regex_part}{re.escape(ext)}$")

        max_version = 0
        try:
            for f in os.listdir(directory):
                match = version_regex.match(f)
                if match:
                    version = int(match.group(1))
                    if version > max_version:
                        max_version = version
        except FileNotFoundError:
            # The directory might not exist yet, which is fine.
            pass

        return max_version + 1

    def save_new_version(self, base_path, data):
        """
        Saves data to a new, versioned file.

        Args:
            base_path (str): The base file path (e.g., 'data/listing.json').
            data (dict or str): The data to be saved.

        Returns:
            str: The full path of the newly created versioned file, or None on failure.
        """
        try:
            next_version = self._get_next_version(base_path)

            directory, filename = os.path.split(base_path)
            base_name, ext = os.path.splitext(filename)

            # Construct the new versioned filename
            version_tag = self.pattern.format(version=next_version)
            new_filename = f"{base_name}{version_tag}{ext}"
            new_filepath = os.path.join(directory, new_filename)

            logging.info(f"Saving new version: '{new_filepath}'")

            # Save the data (assuming JSON for this example, but could be adapted)
            with open(new_filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, dict):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))

            return new_filepath
        except Exception as e:
            logging.error(f"Failed to save new version for '{base_path}'. Error: {e}")
            return None

    def diff_versions(self, file_v1_path, file_v2_path):
        """
        Generates a report on the differences between two JSON file versions.
        (Simplified for demonstration)
        """
        # In a real implementation, a library like 'jsondiff' would be used for a rich diff.
        logging.info(f"Generating diff between '{file_v1_path}' and '{file_v2_path}'.")

        with open(file_v1_path, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file_v2_path, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)

        # This is a very basic diff simulation.
        diff = {
            "added_keys": list(set(data2.keys()) - set(data1.keys())),
            "removed_keys": list(set(data1.keys()) - set(data2.keys())),
            "comment": "This is a simulated diff. Use a proper library for detailed comparison."
        }
        return diff