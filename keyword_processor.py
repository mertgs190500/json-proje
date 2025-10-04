import logging
import json

class KeywordProcessor:

    def _collect(self, seed):
        logging.info("  [Sub-task] Collecting keywords...")
        return [seed, f"{seed} handmade", "cup", "gift"]

    def _filter(self, keywords):
        logging.info("  [Sub-task] Filtering keywords...")
        return [kw for kw in keywords if kw != "gift"]

    def _merge(self, keywords, market_tags, visual_tags):
        logging.info("  [Sub-task] Merging with market and visual data...")
        # Add visual tags to the keyword pool for harmony
        return list(set(keywords + market_tags + visual_tags))

    def _load_weights(self, db_manager):
        """Loads keyword performance weights from the knowledge base."""
        if not db_manager:
            return {}
        db = db_manager.load_db("knowledge_base.json")
        return db.get("keyword_performance_weights", {}) if db else {}

    def _score_and_select(self, keywords, db_manager, external_metrics=None, visual_attributes=None):
        """Scores keywords using a Fusion Model (historical weights + external metrics + visual boost)."""

        historical_weights = self._load_weights(db_manager)
        if external_metrics is None:
            external_metrics = {}
        if visual_attributes is None:
            visual_attributes = []

        scored_keywords = []
        for kw in keywords:
            # 1. Historical Performance Score (default: 1.0)
            hist_score = historical_weights.get(kw, 1.0)

            # 2. External Metric Score (based on Volume, CTR, CR, Competition)
            ext_data = external_metrics.get(kw, {})
            ext_score = 1.0  # Default neutral score
            if ext_data:
                volume = ext_data.get("volume", 0)
                competition = max(ext_data.get("competition", 1), 1) # Avoid division by zero
                ctr = ext_data.get("ctr", 0.01) # Click-through rate
                cr = ext_data.get("cr", 0.01)   # Conversion rate

                # Raw score formula emphasizes high-conversion, high-volume, low-competition keywords
                raw_score = (volume * ctr * cr) / competition
                # Simple normalization to keep the score within a reasonable range (e.g., 0.5 to 2.5)
                ext_score = min(max(raw_score / 5.0, 0.5), 2.5)

            # 3. Final Fusion Score (blending historical and external scores)
            # Formula: (Historical * 0.3) + (External * 0.7)
            final_score = (hist_score * 0.3) + (ext_score * 0.7)

            # 4. Visual Boost
            if visual_attributes and kw in visual_attributes:
                final_score *= 1.2  # Apply boost factor
                logging.info(f"  [Visual Boost] Applied boost to '{kw}'. New score: {final_score:.2f}")

            scored_keywords.append((kw, final_score))

        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        logging.info("[KeywordProcessor] Advanced Fusion Scoring (Historical + External + Visual) complete.")

        return [kw[0] for kw in scored_keywords]

    def execute(self, inputs, context, db_manager=None):
        """
        Consolidated keyword preparation process with visual and performance intelligence.
        """
        logging.info("[KeywordProcessor] Intelligent preparation initiated.")

        seed = inputs.get("seed")
        market_tags = inputs.get("market_tags", [])
        visual_tags = inputs.get("visual_tags", [])
        external_metrics = inputs.get("external_metrics", {})
        visual_attributes = inputs.get("visual_attribute_suggestions", []) # NEW: Get visual attributes

        # Internal data flow
        collected = self._collect(seed)
        filtered = self._filter(collected)
        merged = self._merge(filtered, market_tags, visual_tags)

        # Scoring and selection using the advanced Fusion Model
        selected = self._score_and_select(
            merged,
            db_manager,
            external_metrics,
            visual_attributes=visual_attributes
        )

        # The output must conform to the StrategicKeywordData contract
        output = {
            "coreKeywords": selected[:5],
            "longTailKeywords": selected[5:],
            "metrics": {"totalSearchVolume": len(selected) * 100, "competitorDensity": 0.6}
        }
        logging.info("[KeywordProcessor] Preparation complete.")
        return output