import logging
import json

# It's good practice to wrap optional imports
try:
    from jsonschema import validate
    from jsonschema.exceptions import ValidationError, SchemaError
except ImportError:
    validate = None
    ValidationError = None
    SchemaError = None

class ConfigValidator:
    """
    Validates a JSON configuration file against an internal schema.
    """

    def _get_schema(self, config_data):
        """
        Safely retrieves the internal schema from the configuration data.
        """
        logging.info("--- 00: Retrieving internal schema for validation ---")
        try:
            # Per instructions, the schema is located at a specific path
            schema_path = config_data.get("fs", {}).get("schema_v", {}).get("schema_ref", "")
            if not schema_path.startswith("internal://"):
                raise ValueError(f"Schema reference '{schema_path}' is not an internal reference.")

            # Convert internal path to a JSON path (e.g., internal://schemas/finalset -> /_meta/schemas/finalset)
            json_path = schema_path.replace("internal:/", "/_meta")
            parts = json_path.strip('/').split('/')

            schema = config_data
            for part in parts:
                schema = schema[part]

            logging.info(f"Successfully retrieved internal schema from '{json_path}'.")
            return schema
        except (KeyError, IndexError) as e:
            error_msg = f"HATA: finalv1.json içinde şema bulunamadı. Beklenen yol: '{schema_path}'. Detay: {e}"
            logging.critical(error_msg)
            raise LookupError(error_msg) from e
        except Exception as e:
            error_msg = f"HATA: Şema alınırken beklenmedik bir hata oluştu: {e}"
            logging.critical(error_msg)
            raise RuntimeError(error_msg) from e

    def execute(self, inputs, context):
        """
        Validates the main configuration file against its own internal schema.
        """
        logging.info("--- 00: Performing Configuration Schema Validation ---")

        if not validate:
            error_msg = "HATA: 'jsonschema' kütüphanesi yüklü değil. Yapılandırma doğrulaması yapılamıyor."
            logging.critical(error_msg)
            raise ImportError(error_msg)

        config_file_path = inputs.get("config_file_path")
        if not config_file_path:
            raise ValueError("Config file path not provided in inputs.")

        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            error_msg = f"HATA: '{config_file_path}' dosyası okunamadı veya geçersiz JSON. Hata: {e}"
            logging.critical(error_msg)
            raise

        schema = self._get_schema(config_data)

        try:
            validate(instance=config_data, schema=schema)
            logging.info("OK: finalv1.json dosyası yapısal olarak geçerli.")
            return {"status": "OK", "message": "Configuration is valid."}
        except ValidationError as e:
            # Provide a user-friendly error message
            error_path = " -> ".join(map(str, e.path))
            error_msg = f"HATA: finalv1.json dosyası yapısal olarak geçersiz. Yol: '/{error_path}', Hata: {e.message}"
            logging.critical(error_msg)
            raise
        except SchemaError as e:
            error_msg = f"HATA: Dahili şemanın kendisi geçersiz. Lütfen şemayı kontrol edin. Hata: {e.message}"
            logging.critical(error_msg)
            raise