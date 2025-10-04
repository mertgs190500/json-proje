import json
import logging
import os
from datetime import datetime, timezone, timedelta

class KnowledgeManager:
    def __init__(self, version_controller, base_path='outputs/knowledge_base.json', ttl_days=30):
        self.version_controller = version_controller
        self.base_path = base_path
        self.ttl = timedelta(days=ttl_days)
        self.db = self._load_db()

        if self.db is None:
            self.db = {
                "session_state": {},
                "learned_insights": [],
                "performance_metrics": []
            }
            self._save_db("Initial knowledge base creation")

        logging.info(f"KnowledgeManager initialized. Base path: {self.base_path}")

    def _load_db(self):
        latest_db_path = self.version_controller.get_latest_version_path(self.base_path)
        if latest_db_path and os.path.exists(latest_db_path):
            logging.info(f"Loading latest knowledge base from: {latest_db_path}")
            try:
                with open(latest_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data.setdefault("session_state", {})
                    data.setdefault("learned_insights", [])
                    data.setdefault("performance_metrics", [])
                    return data
            except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
                logging.error(f"Failed to load or parse {latest_db_path}: {e}. Returning None.", exc_info=True)
                return None

        logging.warning(f"No existing knowledge base found for base path '{self.base_path}'. Will create a new one.")
        return None

    def _save_db(self, reason='Persisting updated knowledge base'):
        try:
            self.version_controller.save_with_metadata(
                base_path=self.base_path,
                data=self.db,
                actor='knowledge_manager.py',
                reason=reason
            )
        except Exception as e:
            logging.error(f"Knowledge base could not be saved: {e}", exc_info=True)

    def _is_expired(self, timestamp_str):
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) - timestamp > self.ttl
        except (ValueError, TypeError):
            return False

    def set_session_state(self, key, value):
        self.db["session_state"][key] = value
        self._save_db(f"Update session state: Set '{key}'")

    def get_session_state(self, key=None):
        if key:
            return self.db["session_state"].get(key)
        return self.db["session_state"]

    def add_insight(self, key, value, source_id, confidence):
        if not (0.0 <= confidence <= 1.0):
            confidence = max(0.0, min(1.0, confidence))
        insight = {
            "key": key,
            "value": value,
            "source_id": source_id,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        self.db["learned_insights"].append(insight)
        self._save_db(f"Add new insight: '{key}' from '{source_id}'")

    def get_latest_insight(self, key, ignore_expired=True):
        relevant_insights = sorted(
            [i for i in self.db["learned_insights"] if i.get("key") == key],
            key=lambda x: x.get("timestamp"),
            reverse=True
        )
        if not relevant_insights:
            return None
        for insight in relevant_insights:
            if ignore_expired and self._is_expired(insight.get("timestamp")):
                continue
            return insight
        return None

    def find_insights_by_source(self, source_id):
        return [
            insight for insight in self.db["learned_insights"]
            if insight.get("source_id") == source_id
        ]

    def get_all_insights(self):
        return self.db.get("learned_insights", [])