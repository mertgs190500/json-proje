import logging
import pandas as pd
from collections import Counter

class MarketAnalyzer:
    def execute(self, inputs, context, db_manager=None):
        """
        Analyzes market data based on dynamic rules loaded from the knowledge base.
        """
        logging.info("[MarketAnalyzer] Starting market analysis.")

        # Load product data using the data_loader module's output
        # The input key 'product_data' must match the output of the data loader step in the config
        product_data = inputs.get("product_data")
        if not product_data:
            logging.error("[MarketAnalyzer] No product data provided in inputs.")
            return {"status": "error", "message": "Product data is missing."}

        # The rules are expected to be in the database, managed by DBManager
        if not db_manager:
            logging.error("[MarketAnalyzer] DBManager is not available.")
            return {"status": "error", "message": "Database manager is missing."}

        # Fetch analysis rules from the 'rule_definitions' section of the knowledge base
        rules = db_manager.get("rule_definitions", {}).get("market_analysis_rules", [])
        if not rules:
            logging.warning("[MarketAnalyzer] No market analysis rules found in the knowledge base.")
            return {"status": "no_rules", "message": "No analysis rules were configured."}

        logging.info(f"[MarketAnalyzer] Applying {len(rules)} rules.")

        # Example of a simple rule application: Find popular items based on 'views'
        # This can be expanded to a more complex rule engine.
        analysis_results = {}
        for rule in rules:
            if rule["type"] == "popularity_contest":
                threshold = rule.get("parameters", {}).get("min_views", 1000)
                popular_products = [
                    p for p in product_data
                    if p.get("product_details", {}).get("views", 0) > threshold
                ]
                analysis_results["popular_products"] = {
                    "count": len(popular_products),
                    "products": [p["product_name"] for p in popular_products]
                }

            elif rule["type"] == "category_distribution":
                categories = [p.get("category") for p in product_data if "category" in p]
                category_counts = Counter(categories)
                analysis_results["category_distribution"] = dict(category_counts)

        logging.info("[MarketAnalyzer] Dynamic rule-based analysis completed.")
        return {
            "status": "success",
            "analysis_summary": analysis_results
        }