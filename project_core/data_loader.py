import logging
import json

class DataLoader:
    def execute(self, inputs, context, db_manager=None):
        file_path = inputs.get("file_path")
        logging.info(f"[DataLoader] Harici veri yükleniyor: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info("[DataLoader] Veri başarıyla yüklendi.")
            return data
        except Exception as e:
            logging.error(f"[DataLoader] Dosya yüklenemedi: {file_path}. Hata: {e}")
            return None