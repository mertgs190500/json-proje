import os
import json
import re
import logging
import hashlib
import tempfile
import shutil
from datetime import datetime, timezone

class VersionControl:
    def __init__(self, versioning_config):
        self.pattern = versioning_config.get("pattern", "default_v{N}_{sha12}.json")
        self.base_dir = versioning_config.get("base_dir", "outputs/fs")
        self.ver_dir = versioning_config.get("ver_dir", os.path.join(self.base_dir, "ver"))
        os.makedirs(self.ver_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def _get_next_version(self, base_name, ext):
        max_version = 0
        version_regex = re.compile(f"^{re.escape(base_name)}.*?_v(\\d+).*?{re.escape(ext)}$")
        try:
            for f in os.listdir(self.ver_dir):
                match = version_regex.match(f)
                if match:
                    version = int(match.group(1))
                    if version > max_version:
                        max_version = version
        except FileNotFoundError:
            pass
        return max_version + 1

    def save_new_version(self, base_path, data):
        try:
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
            base_name, ext = os.path.splitext(os.path.basename(base_path))
            if not ext: ext = default_ext
            next_version = self._get_next_version(base_name, ext)
            pattern_name_part, _ = os.path.splitext(self.pattern)
            temp_pattern = pattern_name_part.replace('{N}', '<<VERSION>>').replace('{sha12}', '<<SHA12>>')
            time_formatted_pattern = datetime.now(timezone.utc).strftime(temp_pattern)
            final_pattern_part = time_formatted_pattern.replace('<<VERSION>>', '{N}').replace('<<SHA12>>', '{sha12}')
            filename_part = final_pattern_part.format(N=next_version, sha12=sha256_hash[:12])
            final_filename = f"{base_name}_{filename_part}{ext}"
            final_filepath = os.path.join(self.ver_dir, final_filename)

            temp_dir = os.path.join(self.base_dir, "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(suffix=".tmp", dir=temp_dir)

            with os.fdopen(fd, 'wb') as temp_file:
                temp_file.write(serialized_data)
            shutil.move(temp_path, final_filepath)

            self.logger.info(f"Successfully saved new version: {final_filepath}")
            return {"filepath": final_filepath, "version": next_version, "sha256": sha256_hash}
        except Exception as e:
            self.logger.error(f"Failed to save new version for '{base_path}': {e}", exc_info=True)
            raise

    def save_with_metadata(self, base_path, data, actor, reason):
        save_result = self.save_new_version(base_path, data)
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": save_result["version"],
            "sha256": save_result["sha256"],
            "actor": actor,
            "reason": reason,
            "source_file": save_result["filepath"]
        }
        meta_filepath = os.path.splitext(save_result["filepath"])[0] + ".meta.json"
        try:
            with open(meta_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved metadata: {meta_filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save metadata for '{meta_filepath}': {e}", exc_info=True)
        return save_result

    def get_latest_version_path(self, base_path):
        base_name, ext = os.path.splitext(os.path.basename(base_path))
        if not ext: ext = ".json"
        version_regex = re.compile(f"^{re.escape(base_name)}.*?_v(\\d+).*?(?<!\\.meta){re.escape(ext)}$")
        latest_version = -1
        latest_file = None
        if not os.path.exists(self.ver_dir):
            return None
        for f in os.listdir(self.ver_dir):
            match = version_regex.match(f)
            if match:
                version = int(match.group(1))
                if version > latest_version:
                    latest_version = version
                    latest_file = os.path.join(self.ver_dir, f)
        return latest_file