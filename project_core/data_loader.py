import json
import logging

class DataLoader:
    def execute(self, inputs, context, db_manager=None):
        file_path = inputs.get("file_path")
        if not file_path:
            logging.error("[DataLoader] 'file_path' not provided in inputs.")
            raise ValueError("DataLoader requires 'file_path' in its inputs.")

        logging.info(f"[DataLoader] Loading data from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"[DataLoader] Successfully loaded data from {file_path}.")
            return data
        except FileNotFoundError:
            logging.error(f"[DataLoader] File not found: {file_path}")
            raise
        except Exception as e:
            logging.error(f"[DataLoader] An unexpected error occurred while loading {file_path}: {e}")
            raise