import logging
import json

class FeedbackProcessor:
    def execute(self, inputs, context, db_manager=None):
        """
        Processes performance data and updates the knowledge base via the DBManager.
        """
        logging.info("[FeedbackProcessor] Feedback loop initiated.")

        if not db_manager:
            logging.error("[FeedbackProcessor] DBManager was not provided. Cannot update knowledge base.")
            return {"status": "failed", "reason": "DBManager missing"}

        # 1. Load the knowledge base
        kb = db_manager.load_db("knowledge_base.json")
        if kb is None:
            # If the file doesn't exist or is invalid, start with a fresh structure
            kb = {"keyword_performance_weights": {}}
        weights = kb.get("keyword_performance_weights", {})

        # 2. Analyze performance data (simple algorithm for demonstration)
        performance_data = inputs.get("performance_data", [])
        if not performance_data:
            logging.info("[FeedbackProcessor] No performance data provided. Nothing to update.")
            return {"status": "no_data"}

        for item in performance_data:
            keyword = item.get("keyword")
            sales = item.get("sales", 0)
            traffic = item.get("traffic", 0)

            if not keyword:
                continue

            if traffic > 0:
                conversion_rate = sales / traffic
                # Adjust weight based on conversion rate
                if conversion_rate > 0.05: # High CR (>5%)
                    weights[keyword] = round(weights.get(keyword, 1.0) * 1.1, 2) # Increase weight by 10%
                elif conversion_rate < 0.01: # Low CR (<1%)
                    weights[keyword] = round(weights.get(keyword, 1.0) * 0.9, 2) # Decrease weight by 10%

        # 3. Save the updated knowledge base
        kb["keyword_performance_weights"] = weights
        db_manager.save_db("knowledge_base.json", kb)
        logging.info("[FeedbackProcessor] Knowledge base has been updated.")
        return {"status": "updated"}