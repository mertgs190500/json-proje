import json
import logging
import os
import re
from datetime import datetime, timezone, timedelta

class KnowledgeManager:
    """
    Manages a structured, time-stamped, and confidence-scored knowledge base.
    All write operations are versioned via the VersionControl module.
    """
    def __init__(self, version_controller, base_path='outputs/knowledge_base.json', ttl_days=30):
        """
        Initializes the KnowledgeManager with a version controller.

        Args:
            version_controller: An instance of the VersionControl class.
            base_path (str): The base path for the knowledge base file.
            ttl_days (int): Time-to-live for insights in days.
        """
        self.version_controller = version_controller
        self.base_path = base_path
        self.ttl = timedelta(days=ttl_days)
        self.db = self._load_db()

        # If the database was empty (i.e., no previous versions found), save the initial structure.
        if not self.db.get("learned_insights") and not self.db.get("session_state"):
             self._save_db("Initial knowledge base creation")

        logging.info(f"KnowledgeManager initialized. Base path: {self.base_path}")

    def _find_latest_db(self):
        """Finds the most recent version of the knowledge base file."""
        ver_dir = self.version_controller.ver_dir
        base_name = os.path.splitext(os.path.basename(self.base_path))[0]

        # Regex to capture version number from filenames like 'knowledge_base_..._v123.json'
        pattern = re.compile(f"^{re.escape(base_name)}.*?_v(\\d+).*?.json$")

        latest_version = -1
        latest_file = None

        if not os.path.exists(ver_dir):
            return None

        for filename in os.listdir(ver_dir):
            match = pattern.match(filename)
            if match:
                version = int(match.group(1))
                if version > latest_version:
                    latest_version = version
                    latest_file = os.path.join(ver_dir, filename)

        return latest_file

    def _load_db(self):
        """Loads the most recent version of the JSON database from the versioned directory."""
        latest_db_path = self._find_latest_db()
        if latest_db_path:
            logging.info(f"Loading latest knowledge base from: {latest_db_path}")
            try:
                with open(latest_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure all required sections exist for forward compatibility
                    data.setdefault("session_state", {})
                    data.setdefault("learned_insights", [])
                    data.setdefault("performance_metrics", [])
                    return data
            except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
                logging.error(f"Failed to load or parse {latest_db_path}: {e}. Starting fresh.", exc_info=True)

        logging.warning(f"No existing knowledge base found for base path '{self.base_path}'. Creating a new one.")
        return {
            "session_state": {},
            "learned_insights": [],
            "performance_metrics": []
        }

    def _save_db(self, reason='Persisting updated knowledge base across session.'):
        """Saves the current state of the database using the version controller."""
        try:
            self.version_controller.save_with_metadata(
                base_path=self.base_path,
                data=self.db,
                actor='knowledge_manager.py',
                reason=reason
            )
        except Exception as e:
            logging.error(f"Knowledge base could not be saved via VersionController: {e}", exc_info=True)

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
        self._save_db(f"Update session state: Set '{key}'")
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
        self._save_db(f"Add new insight: '{key}' from '{source_id}'")
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

    def get_all_insights(self):
        """Returns all insights from the knowledge base."""
        return self.db.get("learned_insights", [])