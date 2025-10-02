import logging
import json
import os

class DataLoader:
    def execute(self, inputs, context, db_manager=None):
        """
        Reads a specified file and returns its content.
        For JSON files, it returns a parsed dictionary.
        For other files (like CSV), it returns raw bytes for further processing.
        """
        file_path = inputs.get("file_path")
        if not file_path:
            logging.error("[DataLoader] 'file_path' input is missing.")
            return None

        logging.info(f"[DataLoader] Loading data from: {file_path}")

        if not os.path.exists(file_path):
            logging.error(f"[DataLoader] File not found: {file_path}")
            return None

        _, file_extension = os.path.splitext(file_path)

        try:
            if file_extension.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"[DataLoader] JSON file '{file_path}' loaded and parsed successfully.")
                return data
            else:  # Assume CSV or other raw file types
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                logging.info(f"[DataLoader] Raw file '{file_path}' loaded successfully ({len(raw_data)} bytes).")
                # Return a dict for consistency, passing along critical info
                return {"raw_content": raw_data, "file_path": file_path}
        except Exception as e:
            logging.error(f"[DataLoader] Failed to load file: {file_path}. Error: {e}", exc_info=True)
            return None