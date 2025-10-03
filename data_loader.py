import logging
import json
import os

class DataLoader:
    def execute(self, inputs, context, db_manager=None):
        """
        Reads a specified file and returns its content in a standardized dictionary format.
        - For JSON files, 'data' contains the parsed dictionary.
        - For other files (like CSV), 'data' contains raw bytes.
        """
        file_path = inputs.get("file_path")
        if not file_path:
            message = "'file_path' input is missing."
            logging.error(f"[DataLoader] {message}")
            return {'status': 'error', 'data': None, 'message': message}

        logging.info(f"[DataLoader] Loading data from: {file_path}")

        if not os.path.exists(file_path):
            message = f"File not found: {file_path}"
            logging.error(f"[DataLoader] {message}")
            return {'status': 'error', 'data': None, 'message': message}

        _, file_extension = os.path.splitext(file_path)

        try:
            if file_extension.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                message = f"JSON file '{file_path}' loaded and parsed successfully."
                logging.info(f"[DataLoader] {message}")
                return {'status': 'success', 'data': data, 'message': message}
            else:  # Assume CSV or other raw file types
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                message = f"Raw file '{file_path}' loaded successfully ({len(raw_data)} bytes)."
                logging.info(f"[DataLoader] {message}")
                return {'status': 'success', 'data': raw_data, 'message': message}
        except Exception as e:
            message = f"Failed to load file: {file_path}. Error: {e}"
            logging.error(f"[DataLoader] {message}", exc_info=True)
            return {'status': 'error', 'data': None, 'message': message}