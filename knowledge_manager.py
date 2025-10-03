import json
import logging
import os
from datetime import datetime, timezone, timedelta

class KnowledgeManager:
    """
    Manages a structured, time-stamped, and confidence-scored knowledge base.
    """
    def __init__(self, db_path='knowledge_base.json', ttl_days=30):
        self.db_path = db_path
        self.ttl = timedelta(days=ttl_days)

        # Check for existence before loading.
        db_exists = os.path.exists(self.db_path)
        self.db = self._load_db()

        # If the db did not exist, save the newly created default structure.
        if not db_exists:
            self._save_db()

        logging.info(f"KnowledgeManager başlatıldı. Veritabanı: {self.db_path}")

    def _load_db(self):
        """Loads the JSON database from the file, ensuring it has the required structure."""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all required sections exist
                if "session_state" not in data:
                    data["session_state"] = {}
                if "learned_insights" not in data:
                    data["learned_insights"] = []
                if "performance_metrics" not in data:
                    data["performance_metrics"] = []
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"{self.db_path} bulunamadı veya geçersiz. Varsayılan yapı oluşturuluyor.")
            return {
                "session_state": {},
                "learned_insights": [],
                "performance_metrics": []
            }

    def _save_db(self):
        """Saves the current state of the database to the file."""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Bilgi tabanı kaydedilemedi: {self.db_path}. Hata: {e}")

    def _is_expired(self, timestamp_str):
        """Checks if a timestamp is older than the defined TTL."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) - timestamp > self.ttl
        except (ValueError, TypeError):
            return False # If timestamp is invalid, treat as not expired

    def set_session_state(self, key, value):
        """Sets a value in the session_state section."""
        self.db["session_state"][key] = value
        self._save_db()
        logging.info(f"Oturum durumu güncellendi: '{key}' = '{value}'")

    def get_session_state(self, key=None):
        """Gets a value from the session_state, or the entire state if key is None."""
        if key:
            return self.db["session_state"].get(key)
        return self.db["session_state"]

    def add_insight(self, key, value, source_id, confidence):
        """
        Adds a new piece of learned information to the knowledge base.
        Ensures that insights are time-stamped and have a source and confidence score.
        """
        if not (0.0 <= confidence <= 1.0):
            logging.warning(f"Geçersiz güvenilirlik puanı: {confidence}. 0.0-1.0 arasında olmalı.")
            confidence = max(0.0, min(1.0, confidence))

        insight = {
            "key": key,
            "value": value,
            "source_id": source_id,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        self.db["learned_insights"].append(insight)
        self._save_db()
        logging.info(f"Yeni bilgi eklendi: Anahtar='{key}', Kaynak='{source_id}'")

    def get_latest_insight(self, key, ignore_expired=True):
        """
        Retrieves the most recent, non-expired insight for a given key.
        Returns the full insight object or None if not found.
        """
        relevant_insights = sorted(
            [i for i in self.db["learned_insights"] if i.get("key") == key],
            key=lambda x: x.get("timestamp"),
            reverse=True
        )

        if not relevant_insights:
            return None

        for insight in relevant_insights:
            if ignore_expired and self._is_expired(insight.get("timestamp")):
                logging.warning(f"Eski bilgi bulundu (ve atlandı): Anahtar='{key}', Zaman Damgası='{insight.get('timestamp')}'")
                continue
            return insight # Return the first one that is not expired

        return None # All relevant insights were expired

    def find_insights_by_source(self, source_id):
        """
        Finds all insights that originated from a specific source_id.
        """
        return [
            insight for insight in self.db["learned_insights"]
            if insight.get("source_id") == source_id
        ]