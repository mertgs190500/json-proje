import time
import logging

class SessionManager:
    """
    Manages the overall state of the workflow, including time and update counters,
    to ensure safe and controlled execution.
    """
    def __init__(self, session_policy=None):
        """
        Initializes the session manager with policies for timeout and updates.

        Args:
            session_policy (dict): A dictionary containing session rules,
                                   e.g., {'timeout_seconds': 3600, 'max_updates': 1000}.
        """
        if session_policy is None:
            session_policy = {}

        self.start_time = time.time()

        # Get policies from config or set safe defaults
        self.timeout_seconds = session_policy.get("timeout_seconds", 3600)  # Default: 1 hour
        self.max_updates = session_policy.get("max_updates", 1000)      # Default: 1000 updates

        self.update_counter = 0
        logging.info(f"Session Manager initialized. Timeout: {self.timeout_seconds}s, Max Updates: {self.max_updates}.")

    def log_update(self):
        """Increments the update counter. Should be called after a significant state change."""
        self.update_counter += 1

    def check_status(self):
        """
        Checks if the session has timed out or exceeded the maximum update count.

        Returns:
            tuple: A tuple containing a status string ('STATUS_OK', 'TIMEOUT_REACHED',
                   'MAX_UPDATES_REACHED') and a descriptive message.
        """
        # 1. Check for timeout
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.timeout_seconds:
            message = f"Session timed out after {elapsed_time:.2f} seconds (limit: {self.timeout_seconds}s)."
            logging.warning(message)
            return "TIMEOUT_REACHED", message

        # 2. Check for max updates
        if self.update_counter > self.max_updates:
            message = f"Maximum update count of {self.max_updates} exceeded."
            logging.warning(message)
            return "MAX_UPDATES_REACHED", message

        return "STATUS_OK", "Session is within operational limits."

    def check_api_usage(self, service_name, tokens_to_use=1):
        """
        Simulates checking API token usage against limits.
        In a real implementation, this would interact with a persistent token store.
        """
        # This is a simplified simulation for demonstration.
        logging.debug(f"Token check for '{service_name}': {tokens_to_use} tokens requested. OK.")
        return True