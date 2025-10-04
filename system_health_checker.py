import logging
import importlib.metadata
import os
from packaging.version import parse as parse_version

# It's good practice to wrap optional imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class SystemHealthChecker:
    """
    Performs system health checks at the beginning of a workflow, such as
    checking dependency versions and API accessibility.
    """

    def _check_dependencies(self, required_versions):
        """
        Checks if installed Python packages meet minimum version requirements.
        Logs a warning for outdated packages but does not halt execution.
        """
        logging.info("--- 0a: Performing Dependency Version Check ---")
        warnings = []
        if not required_versions:
            logging.info("No dependency versions to check.")
            return warnings

        for package, min_version_str in required_versions.items():
            try:
                installed_version_str = importlib.metadata.version(package)
                installed_version = parse_version(installed_version_str)
                min_version = parse_version(min_version_str)

                if installed_version < min_version:
                    warning_msg = (
                        f"UYARI: '{package}' kütüphanesinin yüklü sürümü ({installed_version_str}), "
                        f"gereken minimum sürümden ({min_version_str}) daha eski. "
                        f"Bu durum beklenmedik hatalara yol açabilir."
                    )
                    logging.warning(warning_msg)
                    warnings.append(warning_msg)
                else:
                    logging.info(f"OK: '{package}' version {installed_version_str} meets requirement >= {min_version_str}.")

            except importlib.metadata.PackageNotFoundError:
                # This is a more severe issue, but per instructions, we only warn.
                # In a real-world scenario, this might be a critical error.
                warning_msg = f"UYARI: Gerekli kütüphane '{package}' bulunamadı. Bu adım atlanacak."
                logging.warning(warning_msg)
                warnings.append(warning_msg)
        return warnings

    def _check_api_accessibility(self):
        """
        Performs a health check on the Gemini API to ensure it's accessible.
        This is a critical check; failure will halt the workflow.
        """
        logging.info("--- 0a: Performing API Accessibility Health Check ---")
        if not genai:
            error_msg = "HATA: 'google-generativeai' kütüphanesi yüklü değil. API kontrolü yapılamıyor."
            logging.critical(error_msg)
            raise ImportError(error_msg)

        # The API key is expected to be set in the environment as GOOGLE_API_KEY
        if not os.getenv("GOOGLE_API_KEY"):
            error_msg = "HATA: GOOGLE_API_KEY ortam değişkeni ayarlanmamış. Gemini API'ye erişilemiyor."
            logging.critical(error_msg)
            raise ValueError(error_msg)

        try:
            # A lightweight, non-quota-consuming call to check connectivity and auth.
            genai.list_models()
            logging.info("OK: Gemini API'ye başarıyla erişildi.")
            return True
        except Exception as e:
            error_msg = f"HATA: Gemini API'ye erişilemiyor. Lütfen API anahtarınızı ve internet bağlantınızı kontrol edin. Detay: {e}"
            logging.critical(error_msg)
            raise ConnectionError(error_msg)

    def execute(self, inputs, context):
        """
        Runs all system health checks defined in the module.
        """
        logging.info("--- Running System Health Checks ---")

        # 1. Dependency Version Check (non-critical, logs warnings)
        required_versions = inputs.get("required_dependency_versions", {})
        dependency_warnings = self._check_dependencies(required_versions)

        # 2. API Health Check (critical, raises exception on failure)
        self._check_api_accessibility()

        logging.info("--- System Health Checks Passed ---")

        return {
            "status": "OK",
            "dependency_warnings": dependency_warnings,
            "api_status": "OK"
        }