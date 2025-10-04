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
            return pd.Series([0.5] * len(df), index=df.index)
        return (df[column_name] - min_val) / (max_val - min_val)

    def _extract_keywords(self, series, top_n=50):
        """Extracts and counts keywords from a pandas Series of text."""
        series = series.dropna().astype(str)
        all_text = ' '.join(series).lower()
        words = re.findall(r'\b\w+\b', all_text)
        words = [word for word in words if len(word) > 2]
        return [item[0] for item in Counter(words).most_common(top_n)]

    def analyze_popular_listings(self, df_popular):
        """
        Analyzes the 'Top Listings' dataset to calculate product scores
        and identify popular keywords.
        """
        logging.info("Analyzing popular listings...")
        metric_cols = ['Views', 'Favorites', 'Quantity']
        for col in metric_cols:
            if col not in df_popular.columns:
                logging.warning(f"'{col}' column not found in popular listings. Filling with 0.")
                df_popular[col] = 0
            else:
                df_popular[col] = pd.to_numeric(df_popular[col], errors='coerce').fillna(0)
        df_popular['norm_views'] = self._normalize_column(df_popular, 'Views')
        df_popular['norm_favorites'] = self._normalize_column(df_popular, 'Favorites')
        df_popular['norm_quantity'] = self._normalize_column(df_popular, 'Quantity')
        df_popular['product_score'] = (
            df_popular['norm_views'] * 0.5 +
            df_popular['norm_favorites'] * 0.3 +
            df_popular['norm_quantity'] * 0.2
        )
        popular_products_top = df_popular.sort_values(
            by='product_score', ascending=False
        ).head(10)[['Title', 'product_score']].to_dict('records')
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
        competitor_themes = self._extract_keywords(
            pd.concat([df_competitors['Title'], df_competitors.get('Tags', pd.Series(dtype=str))]),
            top_n=30
        )
        df_competitors['Price'] = pd.to_numeric(df_competitors['Price'], errors='coerce')
        pricing_signals = {
            "avg_price": df_competitors['Price'].mean(),
            "median_price": df_competitors['Price'].median(),
            "min_price": df_competitors['Price'].min(),
            "max_price": df_competitors['Price'].max(),
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

    def _generate_ad_strategy(self, row):
        """Generates advertising strategy suggestions for a keyword."""
        # Match Type Suggestion Logic
        if row.get('Long-tail keyword', 'No') == 'Yes':
            match_type = 'Exact'
        else:
            match_type = 'Phrase'

        # Bid Strategy Suggestion Logic
        competition_norm = row.get('competition_norm', 0.5)
        search_volume_norm = row.get('search_volume_norm', 0.5)

        bid_score = (1 - competition_norm) * 0.6 + search_volume_norm * 0.4

        if bid_score > 0.65:
            bid_strategy = 'High'
        elif bid_score > 0.35:
            bid_strategy = 'Medium'
        else:
            bid_strategy = 'Low'

        return {
            "match_type_suggestion": match_type,
            "bid_strategy_suggestion": bid_strategy
        }

    def aggregate_market_insights(self, popular_analysis, competitor_analysis, df_similar_keywords, product_info):
        """
        Aggregates all insights to find keyword gaps and create ad seeds with strategy suggestions.
        """
        logging.info("Aggregating market insights...")

        # Prepare data from df_similar_keywords
        if 'Keyword' not in df_similar_keywords.columns:
            logging.error("'Keyword' column not found in similar keywords data. Cannot proceed.")
            return {}

        df_similar_keywords['Search volume'] = pd.to_numeric(df_similar_keywords['Search volume'], errors='coerce').fillna(0)
        df_similar_keywords['Competition'] = pd.to_numeric(df_similar_keywords['Competition'], errors='coerce').fillna(0)
        df_similar_keywords['search_volume_norm'] = self._normalize_column(df_similar_keywords, 'Search volume')
        df_similar_keywords['competition_norm'] = self._normalize_column(df_similar_keywords, 'Competition')

        similar_kws_df = df_similar_keywords.set_index('Keyword')

        popular_kws = set(popular_analysis.get('popular_keywords_top', []))
        competitor_kws = set(competitor_analysis.get('competitor_signals', {}).get('main_themes', []))
        demand_kws = set(self._extract_keywords(df_similar_keywords['Keyword'], top_n=100))

        supply_kws = popular_kws.union(competitor_kws)
        keyword_gaps = list(demand_kws - supply_kws)

        # Combine seeds and create strategy suggestions
        positive_seed_keywords = list(dict.fromkeys(list(demand_kws.intersection(popular_kws)) + keyword_gaps))

        ads_seed_positive = []
        for keyword in positive_seed_keywords:
            if keyword in similar_kws_df.index:
                row = similar_kws_df.loc[keyword]
                strategy = self._generate_ad_strategy(row)
                ads_seed_positive.append({
                    "keyword": keyword,
                    **strategy
                })

        ads_seed_negative = list(competitor_kws - popular_kws - demand_kws)

        # Task 2.2: Identify potential negative keywords from demand data based on product attributes.
        proactive_negative_candidates = set()
        product_material = product_info.get("material", "").lower() if isinstance(product_info.get("material"), str) else ""
        if "solid gold" in product_material:
            negative_patterns = ["plated", "filled", "vermeil", "kaplama"]
            logging.info(f"Product is 'solid gold'. Identifying candidates from demand keywords with patterns: {negative_patterns}")
            for keyword in demand_kws:
                for pattern in negative_patterns:
                    if pattern in keyword.lower():
                        proactive_negative_candidates.add(keyword)

        market_snapshot = {
            "keyword_gaps": keyword_gaps[:20],
            "market_demand_keywords": list(demand_kws)[:50],
            "market_supply_keywords": list(supply_kws)[:50]
        }
        logging.info("Market insights aggregation complete.")
        return {
            "market_snapshot": market_snapshot,
            "ads_seed_positive": ads_seed_positive,
            "ads_seed_negative": ads_seed_negative,
            "proactive_negative_candidates": list(proactive_negative_candidates)
        }

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution entry point for the market analysis module.
        """
        logging.info("[MarketAnalyzer] Starting market analysis.")
        popular_data = inputs.get("popular_listings_data")
        competitor_data = inputs.get("competitor_listings_data")
        similar_data = inputs.get("similar_keywords_data")
        product_info = inputs.get("product_info", {}) # Get product info from resolved inputs

        if popular_data is None or competitor_data is None or similar_data is None:
            raise ValueError("Missing one or more required datasets (popular, competitor, or similar).")
        try:
            df_popular = pd.DataFrame(popular_data)
            df_competitors = pd.DataFrame(competitor_data)
            df_similar = pd.DataFrame(similar_data)
        except Exception as e:
            logging.error(f"[MarketAnalyzer] Failed to create DataFrames from input data. Error: {e}")
            raise
        popular_analysis = self.analyze_popular_listings(df_popular.copy())
        competitor_analysis = self.analyze_competitor_listings(df_competitors.copy())
        market_insights = self.aggregate_market_insights(popular_analysis, competitor_analysis, df_similar.copy(), product_info)
        final_output = {**popular_analysis, **competitor_analysis, **market_insights}
        logging.info("[MarketAnalyzer] Market analysis finished successfully.")
        return final_output

    def execute_step_7a(self, inputs, context, version_controller):
        """
        Executes Step 7a: Market and Price Forecast analysis.
        """
        logging.info("[MarketAnalyzer] Starting Step 7a: Market and Price Forecast.")
        competitor_signals = inputs.get("competitor_signals", {})
        pricing_data = competitor_signals.get("pricing", {})
        product_info = context.get("product.info", {})
        if not pricing_data or not product_info:
            raise ValueError("Missing pricing data or product info for Step 7a.")

        median_price = pricing_data.get("median_price", 0)
        analysis_summary = {
            "competitor_price_avg": round(pricing_data.get("avg_price", 0), 2),
            "competitor_price_median": round(median_price, 2)
        }

        recommended_tiers = {}
        our_prices = product_info.get("variation_prices", {})
        for variation, price_str in our_prices.items():
            variation_key = variation.replace(" ", "_")
            tiers = []
            if median_price > 0:
                tiers.append({
                    "tier": "Competitive",
                    "price_usd": int(median_price * 0.95),
                    "rationale": f"Pazar medyanının (${median_price:.2f}) %5 altında, hacim odaklı."
                })
                tiers.append({
                    "tier": "Market Average",
                    "price_usd": int(median_price * 1.05),
                    "rationale": f"Pazarın geneliyle uyumlu bir fiyat."
                })
                tiers.append({
                    "tier": "Premium",
                    "price_usd": int(median_price * 1.20),
                    "rationale": f"Kalite algısını ve kâr marjını yükseltecek bir fiyat."
                })
            recommended_tiers[variation_key] = tiers

        final_output = {
            "analysis_summary": analysis_summary,
            "recommended_tiers": recommended_tiers
        }

        save_result = version_controller.save_with_metadata(
            base_path='outputs/market_price_forecast.json',
            data=final_output,
            actor='market_analyzer.py',
            reason='Executed Step 7a: Market and Price Forecast analysis.'
        )
        return save_result