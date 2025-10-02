import logging
import json

class DataLoader:
    def execute(self, inputs, context, db_manager=None):
        """
        Reads a specified JSON file and returns its content.
        """
        file_path = inputs.get("file_path")
        if not file_path:
            logging.error("[DataLoader] 'file_path' input is missing.")
            return None

        logging.info(f"[DataLoader] Loading external data from: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info("[DataLoader] Data loaded successfully.")
            return data
        except Exception as e:
            logging.error(f"[DataLoader] Failed to load file: {file_path}. Error: {e}")
            # Return None to indicate failure, allowing the orchestrator to handle it.
            return None