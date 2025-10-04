import os
import logging

class SystemHealthChecker:
    """
    Checks for the presence of required directories and other system-level prerequisites.
    """
    def __init__(self):
        self.errors = []
        self.required_dirs = [
            "project_core",
            "outputs",
            "source_data",
            "tests"
        ]

    def _check_directory_exists(self, dirpath):
        """Checks if a directory exists."""
        if not os.path.isdir(dirpath):
            self.errors.append(f"Required directory not found: {dirpath}")
            return False
        return True

    def execute(self):
        """
        Runs all system health checks.

        Returns:
            A dictionary with the health status and a list of errors.
        """
        logging.info("Running system health check...")
        self.errors = []

        for d in self.required_dirs:
            self._check_directory_exists(d)

        if self.errors:
            for error in self.errors:
                logging.error(f"[SystemHealthChecker] - {error}")
            return {"status": "FAIL", "errors": self.errors}

        logging.info("System health check successful.")
        return {"status": "PASS", "errors": []}