import logging
import pandas as pd
from datetime import datetime, timezone

class FeedbackProcessor:
    """
    Analyzes post-publication performance data to identify successful and
    unsuccessful strategies, updating the project's knowledge base with these learnings.
    """

    def execute(self, inputs: dict, knowledge_manager, db_manager=None) -> dict:
        """
        Executes the feedback processing logic.

        Args:
            inputs (dict): A dictionary containing the necessary data.
                           - 'performance_data_csv' (str): Path to the performance data CSV.
                           - 'listing_history_json' (str): Path to the JSON file containing
                             the historical data of the listing (title, tags, etc.).
            knowledge_manager: An instance of the KnowledgeManager class.
            db_manager: (Optional) A database manager instance.

        Returns:
            dict: A dictionary containing the status and a summary of the operation.
        """
        logging.info("[FeedbackProcessor] Starting feedback processing for task FEEDBACK-LOOP-01.")

        performance_data_path = inputs.get("performance_data_csv")
        listing_history_path = inputs.get("listing_history_json")

        if not all([performance_data_path, listing_history_path, knowledge_manager]):
            logging.error("[FeedbackProcessor] Missing one or more required inputs: performance_data_csv, listing_history_json, or knowledge_manager.")
            return {"status": "failed", "reason": "Missing required inputs."}

        try:
            # 1. Load Performance Data
            # In a real scenario, this could come from an API or a more structured input.
            # For this task, we simulate reading from a CSV file.
            # The CSV should have columns like: listing_id, date, visits, orders, ad_spend, revenue
            perf_df = pd.read_csv(performance_data_path)

            # 2. Load Listing History (to correlate performance with what was published)
            # This part is simplified. A real implementation would need a robust way
            # to fetch the exact state of the listing when it was published.
            # with open(listing_history_path, 'r', encoding='utf-8') as f:
            #     listing_history = json.load(f)
            # For now, we'll assume the relevant SEO data is in the performance CSV for simplicity.
            # Example columns: listing_id, title, tags (as a comma-separated string)

        except FileNotFoundError as e:
            logging.error(f"[FeedbackProcessor] File not found: {e}")
            return {"status": "failed", "reason": f"File not found: {e.filename}"}
        except Exception as e:
            logging.error(f"[FeedbackProcessor] An error occurred during data loading: {e}")
            return {"status": "failed", "reason": str(e)}

        insights_added = 0

        # 3. Process data and extract insights for each row (each row is a listing's performance)
        for index, row in perf_df.iterrows():
            try:
                visits = row.get('visits', 0)
                orders = row.get('orders', 0)
                ad_spend = row.get('ad_spend', 0.0)
                revenue = row.get('revenue', 0.0)
                title = row.get('title', '')
                tags = str(row.get('tags', '')).split(',')

                # Calculate Key Metrics
                conversion_rate = (orders / visits) if visits > 0 else 0
                roas = (revenue / ad_spend) if ad_spend > 0 else 0

                # 4. Extract Learnings (Insights)
                # This is a simplified rule set. A real system would have more complex logic.

                # Insight 1: Keyword performance based on ROAS
                if ad_spend > 10: # Only consider keywords with significant spend
                    for tag in tags:
                        tag = tag.strip().lower()
                        if not tag: continue

                        # Simple insight: High ROAS is good, low ROAS is bad.
                        confidence = 0.85 if ad_spend > 50 else 0.70 # Higher confidence with more data
                        if roas > 2.0:
                            knowledge_manager.add_insight(
                                key=f"keyword_roas",
                                value={"keyword": tag, "roas": round(roas, 2), "is_successful": True},
                                source_id="FEEDBACK-LOOP-01",
                                confidence=confidence
                            )
                            insights_added += 1
                        elif roas < 0.8:
                             knowledge_manager.add_insight(
                                key=f"keyword_roas",
                                value={"keyword": tag, "roas": round(roas, 2), "is_successful": False},
                                source_id="FEEDBACK-LOOP-01",
                                confidence=confidence
                            )
                             insights_added += 1

                # Insight 2: Title structure performance based on Conversion Rate
                if visits > 100: # Only for listings with enough traffic
                    confidence = 0.90 if visits > 1000 else 0.75
                    # Example rule: Does the title contain a number? (e.g., "Set of 3 Rings")
                    if any(char.isdigit() for char in title):
                        if conversion_rate > 0.02: # 2% CR is good
                             knowledge_manager.add_insight(
                                key="title_structure_contains_number",
                                value={"has_number": True, "conversion_rate": round(conversion_rate, 4), "is_successful": True},
                                source_id="FEEDBACK-LOOP-01",
                                confidence=confidence
                            )
                             insights_added += 1
                        elif conversion_rate < 0.005: # 0.5% CR is bad
                             knowledge_manager.add_insight(
                                key="title_structure_contains_number",
                                value={"has_number": True, "conversion_rate": round(conversion_rate, 4), "is_successful": False},
                                source_id="FEEDBACK-LOOP-01",
                                confidence=confidence
                            )
                             insights_added += 1

            except Exception as e:
                logging.warning(f"[FeedbackProcessor] Could not process row {index}: {e}")
                continue

        logging.info(f"[FeedbackProcessor] Processing complete. Added {insights_added} new insights to the knowledge base.")

        return {
            "status": "success",
            "message": f"Feedback processing complete. {insights_added} new insights added.",
            "insights_added": insights_added
        }