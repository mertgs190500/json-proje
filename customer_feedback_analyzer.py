import logging
import json
import pandas as pd
from csv_ingestor import CsvIngestor
from version_control import VersionControl
from data_loader import DataLoader

class CustomerFeedbackAnalyzer:
    """
    Analyzes customer feedback by merging reviews with order data,
    performing sentiment analysis and theme extraction.
    """

    def __init__(self):
        """Initializes the analyzer."""
        logging.info("CustomerFeedbackAnalyzer initialized.")
        self.version_controller = VersionControl()

    def _analyze_sentiment(self, text):
        """
        Performs simple rule-based sentiment analysis.
        """
        text_lower = text.lower()
        positive_keywords = ["beautiful", "love", "perfect", "good", "great", "excellent"]
        negative_keywords = ["deceiving", "problem", "broken", "weak", "bad", "poor"]

        if any(word in text_lower for word in negative_keywords):
            return "Negative"
        if any(word in text_lower for word in positive_keywords):
            return "Positive"
        return "Neutral"

    def _extract_themes(self, text):
        """
        Extracts simple keyword themes from text.
        This is a placeholder for a more sophisticated theme extraction model.
        """
        # A more advanced implementation would use NLP to find nouns and adjectives.
        # For now, we'll just split the text and remove common stop words.
        stop_words = {"a", "an", "the", "is", "it", "and", "in", "on", "was", "i", "to", "the"}
        words = text.lower().replace(",", "").replace(".", "").split()
        themes = [word for word in words if word not in stop_words and len(word) > 3]
        # In the example "the clasp is weak", this would return ["clasp", "weak"]
        return list(set(themes)) # Return unique themes

    def execute(self, inputs, context=None, knowledge_manager=None):
        """
        Orchestrates the feedback analysis process.

        Args:
            inputs (dict): A dictionary containing 'reviews_path' and 'orders_path'.
            context (dict): The workflow context (not used in this standalone version).
            knowledge_manager (object): The knowledge manager instance (not used).

        Returns:
            dict: A dictionary containing the status and the path to the output file.
        """
        logging.info("Executing Customer Feedback Analysis...")
        reviews_path = inputs.get("reviews_path")
        orders_path = inputs.get("orders_path")
        output_base_path = inputs.get("output_path", "outputs/customer_feedback_analysis.json")

        if not reviews_path or not orders_path:
            return {"status": "error", "message": "Missing 'reviews_path' or 'orders_path' in inputs."}

        # 1. Load Data
        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
            logging.info(f"Successfully loaded {len(reviews_data)} reviews from '{reviews_path}'.")
        except Exception as e:
            return {"status": "error", "message": f"Failed to load reviews.json: {e}"}

        # To use CsvIngestor, we first need the raw content. We can use DataLoader for this.
        loader = DataLoader()
        loader_output = loader.execute({"file_path": orders_path}, context)
        if loader_output["status"] != "success":
             return {"status": "error", "message": f"Failed to load orders CSV using DataLoader: {loader_output['message']}"}

        # Now, ingest the raw content using CsvIngestor
        ingestor = CsvIngestor()
        # This profile is a generic one for this task, assuming common CSV properties.
        ingestor_profile = {
            "description": "Etsy Sold Orders Profile",
            "encoding": ["utf-8", "cp1254", "latin-1"],
            "delimiter_probe": [","],
            "required_fields": ["Order ID", "Item Name"]
        }
        ingestion_result = ingestor.execute(
            {
                "raw_content": loader_output["data"],
                "file_path": orders_path,
                "resolved_profile": ingestor_profile
            },
            context
        )

        if ingestion_result["status"] != "success":
            return {"status": "error", "message": f"Failed to ingest CSV data: {ingestion_result['message']}"}

        orders_df = pd.DataFrame(ingestion_result["data"])
        logging.info(f"Successfully processed {len(orders_df)} orders from '{orders_path}'.")

        # 2. Merge Data
        reviews_df = pd.DataFrame(reviews_data)
        # Ensure order_id types are consistent for merging
        orders_df['Order ID'] = orders_df['Order ID'].astype(str)
        reviews_df['order_id'] = reviews_df['order_id'].astype(str)

        merged_df = pd.merge(
            reviews_df,
            orders_df,
            left_on='order_id',
            right_on='Order ID',
            how='left' # Keep all reviews, even if no matching order is found
        )
        logging.info(f"Successfully merged reviews and orders. Result has {len(merged_df)} rows.")

        # 3. Analyze and Enrich
        merged_df['sentiment'] = merged_df['message'].apply(self._analyze_sentiment)
        merged_df['extracted_themes'] = merged_df['message'].apply(self._extract_themes)
        logging.info("Sentiment analysis and theme extraction complete.")

        # 4. Format Output
        output_data = []
        for _, row in merged_df.iterrows():
            output_data.append({
                "reviewer_name": row.get("reviewer_name"),
                "star_rating": row.get("star_rating"),
                "review_message": row.get("message"),
                "sentiment": row.get("sentiment"),
                "extracted_themes": row.get("extracted_themes"),
                "order_id": row.get("order_id"),
                "item_name": row.get("Item Name", "N/A"), # Handle cases where order might not match
                "item_variations": row.get("Variations", "N/A")
            })

        # 5. Save Output using VersionControl
        saved_path = self.version_controller.save_new_version(output_base_path, output_data)

        if not saved_path:
            return {"status": "error", "message": "Failed to save output file using VersionControl."}

        logging.info(f"Analysis complete. Output saved to '{saved_path}'.")
        return {"status": "success", "message": "Analysis complete.", "output_path": saved_path}

# Example of how this module could be run for testing purposes
if __name__ == '__main__':
    analyzer = CustomerFeedbackAnalyzer()
    # For standalone testing, context and knowledge_manager can be None.
    result = analyzer.execute(
        inputs={
            "reviews_path": "source_data/reviews.json",
            "orders_path": "source_data/EtsySoldOrderItems2025.csv"
        },
        context={},
        knowledge_manager=None
    )
    print(json.dumps(result, indent=2))