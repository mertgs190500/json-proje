import os
import json
import re
import logging
import hashlib
import tempfile
import shutil
from datetime import datetime, timezone

class VersionControl:
    """
    Manages file versioning with integrity checks (hash), metadata, and atomic writes.
    """

    def __init__(self, versioning_config):
        """
        Initializes the version controller.

        Args:
            versioning_config (dict): The configuration object from finalv1.json,
                                      expected to be at fs.ver.
        """
        self.pattern = versioning_config.get("pattern", "default_v{N}_{sha12}.json")
        self.diff_pattern = versioning_config.get("diff_j", {}).get("pattern", "PATCH_%Y%m%d_%H%M%S.diff.json")
        self.base_dir = "outputs/fs" # Or get from config if available
        self.ver_dir = os.path.join(self.base_dir, "ver")
        self.diff_dir = os.path.join(self.base_dir, "diff_j")
        os.makedirs(self.ver_dir, exist_ok=True)
        os.makedirs(self.diff_dir, exist_ok=True)

        log_file = 'daemon.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Version Control initialized with pattern: '{self.pattern}'")

    def _get_next_version(self, base_name, ext):
        """
        Finds the next available version number for a given base name inside the versioned directory.
        """
        max_version = 0
        # Simplified regex to find version numbers like '_v{N}'
        version_regex = re.compile(f"^{re.escape(base_name)}.*?_v(\\d+).*?{re.escape(ext)}$")
        try:
            for f in os.listdir(self.ver_dir):
                match = version_regex.match(f)
                if match:
                    version = int(match.group(1))
                    if version > max_version:
                        max_version = version
        except FileNotFoundError:
            pass  # Directory might not exist yet
        return max_version + 1

    def save_new_version(self, base_path, data):
        """
        Saves data to a new, versioned file using an atomic write operation.
        Handles dicts (serialized to JSON), strings, and raw bytes.

        Args:
            base_path (str): The logical base path for the file (e.g., 'final_set/results.json').
            data (dict | str | bytes): The data to be saved.

        Returns:
            dict: A dictionary containing the filepath, version, and sha256 hash.
        """
        try:
            # 1. Prepare data and calculate hash
            if isinstance(data, dict):
                serialized_data = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8')
                default_ext = '.json'
            elif isinstance(data, str):
                serialized_data = data.encode('utf-8')
                default_ext = ''
            elif isinstance(data, bytes):
                serialized_data = data
                default_ext = ''
            else:
                raise TypeError("Data must be a dictionary, string, or bytes.")

            sha256_hash = hashlib.sha256(serialized_data).hexdigest()

            # 2. Determine file naming
            base_name, ext = os.path.splitext(os.path.basename(base_path))
            if not ext:
                ext = default_ext

            next_version = self._get_next_version(base_name, ext)

            # To handle both strftime directives (e.g., %Y) and format placeholders (e.g., {N}),
            # we need a two-step formatting process. The pattern from config might have a
            # hardcoded extension, which we need to ignore in favor of the one from base_path.

            pattern_name_part, _ = os.path.splitext(self.pattern)

            # Step 1: Temporarily replace the .format() placeholders with unique, safe strings
            # that strftime will ignore.
            temp_pattern = pattern_name_part.replace('{N}', '<<VERSION>>').replace('{sha12}', '<<SHA12>>')

            # Step 2: Now, safely format the time part using strftime
            time_formatted_pattern = datetime.now(timezone.utc).strftime(temp_pattern)

            # Step 3: Restore the .format() placeholders and then format them.
            final_pattern_part = time_formatted_pattern.replace('<<VERSION>>', '{N}').replace('<<SHA12>>', '{sha12}')
            filename_part = final_pattern_part.format(
                N=next_version,
                sha12=sha256_hash[:12]
            )

            # Add base name and the correct extension determined from the base_path
            final_filename = f"{base_name}_{filename_part}{ext}"
            final_filepath = os.path.join(self.ver_dir, final_filename)

            # 3. Atomic Write
            temp_dir = os.path.join(self.base_dir, "tmp")
            os.makedirs(temp_dir, exist_ok=True)

            # Use a temporary file in a dedicated temp directory
            fd, temp_path = tempfile.mkstemp(suffix=".json", dir=temp_dir)

            try:
                with os.fdopen(fd, 'wb') as temp_file:
                    temp_file.write(serialized_data)

                # Move the file atomically
                shutil.move(temp_path, final_filepath)
                self.logger.info(f"Successfully saved new version: {final_filepath}")

            except Exception as e:
                self.logger.error(f"Error during atomic write: {e}", exc_info=True)
                if os.path.exists(temp_path):
                    os.remove(temp_path) # Clean up temp file on failure
                raise

            # 4. Return result dictionary
            return {
                "filepath": final_filepath,
                "version": next_version,
                "sha256": sha256_hash
            }

        except Exception as e:
            self.logger.error(f"Failed to save new version for '{base_path}': {e}", exc_info=True)
            raise

    def save_with_metadata(self, base_path, data, actor, reason):
        """
        Saves a new version and an accompanying metadata file.

        Args:
            base_path (str): The logical base path for the file.
            data (dict): The JSON data to save.
            actor (str): The script or entity performing the action (e.g., 'tag_generator.py').
            reason (str): The reason for this new version.

        Returns:
            dict: The result from save_new_version.
        """
        # First, save the data file to get its details
        save_result = self.save_new_version(base_path, data)

        # Create metadata content
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": save_result["version"],
            "sha256": save_result["sha256"],
            "actor": actor,
            "reason": reason,
            "source_file": save_result["filepath"]
        }

        # Save the metadata file
        meta_filepath = os.path.splitext(save_result["filepath"])[0] + ".meta.json"

        try:
            with open(meta_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved metadata: {meta_filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save metadata for '{meta_filepath}': {e}", exc_info=True)
            # Decide on error handling: maybe delete the data file? For now, just log.

        return save_result