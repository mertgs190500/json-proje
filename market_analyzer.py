import pandas as pd
import logging
from collections import Counter
import re

class MarketAnalyzer:
    """
    Analyzes market data from various sources to identify trends,
    competitor strategies, and keyword opportunities.
    """

    def _normalize_column(self, df, column_name):
        """Normalizes a DataFrame column to a 0-1 scale."""
        if column_name not in df.columns or df[column_name].isnull().all():
            return pd.Series([0] * len(df), index=df.index)
        min_val = df[column_name].min()
        max_val = df[column_name].max()
        if max_val == min_val:
            return pd.Series([0.5] * len(df), index=df.index) # or 0, or 1, depending on desired behavior
        return (df[column_name] - min_val) / (max_val - min_val)

    def _extract_keywords(self, series, top_n=50):
        """Extracts and counts keywords from a pandas Series of text."""
        # Ensure all entries are strings
        series = series.dropna().astype(str)

        # Simple regex to split words, handles common delimiters
        all_text = ' '.join(series).lower()
        words = re.findall(r'\b\w+\b', all_text)

        # Exclude very short words if necessary, can be expanded with a stopword list
        words = [word for word in words if len(word) > 2]

        return [item[0] for item in Counter(words).most_common(top_n)]

    def analyze_popular_listings(self, df_popular):
        """
        Analyzes the 'Top Listings' dataset to calculate product scores
        and identify popular keywords.
        """
        logging.info("Analyzing popular listings...")

        # Ensure required columns exist and are numeric
        metric_cols = ['Views', 'Favorites', 'Quantity'] # Assuming 'Orders' is 'Quantity'
        for col in metric_cols:
            if col not in df_popular.columns:
                logging.warning(f"'{col}' column not found in popular listings. Filling with 0.")
                df_popular[col] = 0
            else:
                df_popular[col] = pd.to_numeric(df_popular[col], errors='coerce').fillna(0)

        # Normalize metrics
        df_popular['norm_views'] = self._normalize_column(df_popular, 'Views')
        df_popular['norm_favorites'] = self._normalize_column(df_popular, 'Favorites')
        df_popular['norm_quantity'] = self._normalize_column(df_popular, 'Quantity')

        # Calculate product score (weights can be tuned)
        df_popular['product_score'] = (
            df_popular['norm_views'] * 0.5 +
            df_popular['norm_favorites'] * 0.3 +
            df_popular['norm_quantity'] * 0.2
        )

        # Sort by score and get top products
        popular_products_top = df_popular.sort_values(
            by='product_score', ascending=False
        ).head(10)[['Title', 'product_score']].to_dict('records')

        # Extract popular keywords from titles and tags
        popular_keywords_top = self._extract_keywords(
            pd.concat([df_popular['Title'], df_popular.get('Tags', pd.Series(dtype=str))]),
            top_n=20
        )

        logging.info("Popular listings analysis complete.")
        return {
            "popular_products_top": popular_products_top,
            "popular_keywords_top": popular_keywords_top
        }

    def analyze_competitor_listings(self, df_competitors):
        """
        Analyzes competitor listings to identify common themes and signals.
        """
        logging.info("Analyzing competitor listings...")

        # Extract themes from competitor titles and tags
        competitor_themes = self._extract_keywords(
            pd.concat([df_competitors['Title'], df_competitors.get('Tags', pd.Series(dtype=str))]),
            top_n=30
        )

        # Generate signals (example: pricing analysis)
        df_competitors['Price'] = pd.to_numeric(df_competitors['Price'], errors='coerce')
        pricing_signals = {
            "avg_price": df_competitors['Price'].mean(),
            "median_price": df_competitors['Price'].median(),
            "price_std_dev": df_competitors['Price'].std()
        }

        competitor_signals = {
            "main_themes": competitor_themes,
            "pricing": pricing_signals
        }

        logging.info("Competitor listings analysis complete.")
        return {
            "competitor_signals": competitor_signals
        }

    def aggregate_market_insights(self, popular_analysis, competitor_analysis, df_similar_keywords):
        """
        Aggregates all insights to find keyword gaps and create ad seeds.
        """
        logging.info("Aggregating market insights...")

        popular_kws = set(popular_analysis.get('popular_keywords_top', []))
        competitor_kws = set(competitor_analysis.get('competitor_signals', {}).get('main_themes', []))

        # Assuming 'Keyword' column in similar keywords data represents demand
        if 'Keyword' not in df_similar_keywords.columns:
            logging.error("'Keyword' column not found in similar keywords data. Cannot find gaps.")
            demand_kws = set()
        else:
            demand_kws = set(self._extract_keywords(df_similar_keywords['Keyword'], top_n=100))

        # Identify keyword gaps: high demand, low supply (not used by competitors)
        supply_kws = popular_kws.union(competitor_kws)
        keyword_gaps = list(demand_kws - supply_kws)

        # Create positive ad seeds: high demand, used by popular listings OR in gaps
        ads_seed_positive = list(demand_kws.intersection(popular_kws)) + keyword_gaps
        # Deduplicate
        ads_seed_positive = list(dict.fromkeys(ads_seed_positive))

        # Create negative ad seeds (example logic: keywords used by competitors but not in popular or demand)
        ads_seed_negative = list(competitor_kws - popular_kws - demand_kws)

        market_snapshot = {
            "keyword_gaps": keyword_gaps[:20], # Top 20 gaps
            "market_demand_keywords": list(demand_kws)[:50],
            "market_supply_keywords": list(supply_kws)[:50]
        }

        logging.info("Market insights aggregation complete.")
        return {
            "market_snapshot": market_snapshot,
            "ads_seed_positive": ads_seed_positive,
            "ads_seed_negative": ads_seed_negative
        }

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution entry point for the market analysis module.
        It converts input lists of dictionaries into pandas DataFrames and then
        analyzes popular, competitor, and similar keyword data.
        """
        logging.info("[MarketAnalyzer] Starting market analysis.")

        # Get data from inputs, which are expected to be lists of dictionaries
        popular_data = inputs.get("popular_listings_data")
        competitor_data = inputs.get("competitor_listings_data")
        similar_data = inputs.get("similar_keywords_data")

        if popular_data is None or competitor_data is None or similar_data is None:
            msg = "Missing one or more required datasets (popular, competitor, or similar)."
            logging.error(f"[MarketAnalyzer] {msg}")
            raise ValueError(msg)

        # Convert lists of dictionaries to pandas DataFrames
        try:
            df_popular = pd.DataFrame(popular_data)
            df_competitors = pd.DataFrame(competitor_data)
            df_similar = pd.DataFrame(similar_data)
        except Exception as e:
            logging.error(f"[MarketAnalyzer] Failed to create DataFrames from input data. Error: {e}")
            raise

        # --- Execute Analysis Steps ---
        popular_analysis = self.analyze_popular_listings(df_popular.copy())
        competitor_analysis = self.analyze_competitor_listings(df_competitors.copy())
        market_insights = self.aggregate_market_insights(
            popular_analysis,
            competitor_analysis,
            df_similar.copy()
        )

        # --- Combine all results ---
        final_output = {
            **popular_analysis,
            **competitor_analysis,
            **market_insights
        }

        logging.info("[MarketAnalyzer] Market analysis finished successfully.")
        return final_output