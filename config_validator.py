import json
import os
import logging

class ConfigValidator:
    """
    Validates the integrity of critical project configuration files.
    """
    def __init__(self):
        self.errors = []
        self.required_files = [
            "project_core/finalv1.json",
            "rule_definitions.json",
            "csv_profiles.json",
            "orchestrator_policy.json",
            "workflow_schema_v2.json",
            "data_contracts.json",
        ]

    def _check_file_exists(self, filepath):
        """Checks if a file exists and is not empty."""
        if not os.path.exists(filepath):
            self.errors.append(f"Configuration file not found: {filepath}")
            return False
        if os.path.getsize(filepath) == 0:
            self.errors.append(f"Configuration file is empty: {filepath}")
            return False
        return True

    def _validate_json_file(self, filepath):
        """Validates that a file is not only present but also valid JSON."""
        if not self._check_file_exists(filepath):
            return False
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError:
            self.errors.append(f"Invalid JSON format in file: {filepath}")
            return False
        except Exception as e:
            self.errors.append(f"Could not read file {filepath}: {e}")
            return False
        return True

    def _validate_main_config_structure(self):
        """Validates the structure of the main config file."""
        filepath = "project_core/finalv1.json"
        if self._validate_json_file(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Check for critical version control configuration
            if 'fs' not in config or 'ver' not in config.get('fs', {}):
                self.errors.append("Critical key 'fs.ver' is missing from project_core/finalv1.json.")

            # Check for export columns configuration
            if 'exp' not in config or 'cols' not in config.get('exp', {}):
                self.errors.append("Key 'exp.cols' for export columns is missing from project_core/finalv1.json.")

    def execute(self):
        """
        Runs all validation checks.

        Returns:
            A dictionary with the validation status and a list of errors.
        """
        logging.info("Running configuration validation...")
        self.errors = []

        # Validate existence and format of all required config files
        for f in self.required_files:
            self._validate_json_file(f)

        # Perform deep validation on the main config file
        self._validate_main_config_structure()

        if self.errors:
            for error in self.errors:
                logging.error(f"[ConfigValidator] - {error}")
            return {"status": "FAIL", "errors": self.errors}

        logging.info("Configuration validation successful.")
        return {"status": "PASS", "errors": []}