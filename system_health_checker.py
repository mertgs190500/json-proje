import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from importlib.metadata import version, PackageNotFoundError
from packaging.version import parse as parse_version

class SystemHealthChecker:
    """
    Checks for the presence of required directories, API connectivity, dependency versions, and other system-level prerequisites.
    """
    def __init__(self):
        """Initializes the checker and loads environment variables."""
        self.errors = []
        self.warnings = []
        self.required_dirs = ["project_core", "outputs", "source_data", "tests"]
        self.required_dependencies = {
            "pandas": "2.0.0",
            "jsonschema": "4.0.0",
            "google-generativeai": "0.5.0"
        }
        self.critical_files = [
            "project_core/finalv1.json",
            "workflow_schema_v2.json",
            "data_contracts.json",
            "rule_definitions.json",
            "csv_profiles.json",
            "orchestrator_policy.json"
        ]
        load_dotenv()

    def _check_file_exists(self, filepath):
        """Checks if a single file exists."""
        if not os.path.isfile(filepath):
            self.errors.append({"level": "BLOCKER", "message": f"Required file not found: {filepath}"})
            return False
        return True

    def _check_directory_exists(self, dirpath):
        """Checks if a directory exists."""
        if not os.path.isdir(dirpath):
            self.errors.append({"level": "BLOCKER", "message": f"Required directory not found: {dirpath}"})
            return False
        return True

    def _check_gemini_api_connectivity(self):
        """Checks connectivity to the Gemini API."""
        logging.info("Checking Gemini API connectivity...")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "YOUR_API_KEY":
            self.errors.append({"level": "BLOCKER", "message": "GEMINI_API_KEY not found or not set in .env file."})
            return
        try:
            genai.configure(api_key=api_key)
            list(genai.list_models())
            logging.info("Gemini API connectivity successful.")
        except Exception as e:
            self.errors.append({"level": "BLOCKER", "message": f"Gemini API connection failed: {e}"})

    def _check_dependency_versions(self):
        """Checks if critical dependencies meet minimum version requirements."""
        logging.info("Checking dependency versions...")
        for package, min_version_str in self.required_dependencies.items():
            try:
                installed_version_str = version(package)
                installed_version = parse_version(installed_version_str)
                min_version = parse_version(min_version_str)
                if installed_version < min_version:
                    self.warnings.append({
                        "level": "WARNING",
                        "message": f"Dependency '{package}' is outdated. Installed: {installed_version}, Required: >={min_version}"
                    })
            except PackageNotFoundError:
                self.errors.append({"level": "BLOCKER", "message": f"Required dependency '{package}' is not installed."})

    def _check_resource_existence(self):
        """Checks for the existence of critical configuration files."""
        logging.info("Checking for existence of critical resource files...")
        for f in self.critical_files:
            self._check_file_exists(f)

    def execute(self):
        """
        Runs all system health checks.

        Returns:
            A dictionary with the health status and a list of errors/warnings.
        """
        logging.info("Running system health check...")
        self.errors = []
        self.warnings = []

        # Prerequisite checks first
        self._check_resource_existence()
        for d in self.required_dirs:
            self._check_directory_exists(d)

        # Dependency Version checks
        self._check_dependency_versions()

        # API connectivity checks
        self._check_gemini_api_connectivity()

        # Log warnings
        for warning in self.warnings:
            logging.warning(f"[SystemHealthChecker] - {warning['level']}: {warning['message']}")

        # Log and return errors
        if self.errors:
            # Deduplicate errors before logging
            unique_errors = [dict(t) for t in {tuple(d.items()) for d in self.errors}]
            for error in unique_errors:
                logging.error(f"[SystemHealthChecker] - {error['level']}: {error['message']}")
            return {"status": "FAIL", "errors": unique_errors, "warnings": self.warnings}

        logging.info("System health check successful.")
        return {"status": "PASS", "errors": [], "warnings": self.warnings}