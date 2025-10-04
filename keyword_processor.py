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

    def _score_and_select(self, keywords, db_manager, external_metrics=None):
        """Scores keywords using a Fusion Model (historical weights + external metrics)."""

        historical_weights = self._load_weights(db_manager)
        if external_metrics is None:
            external_metrics = {}

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
            scored_keywords.append((kw, final_score))

        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        logging.info("[KeywordProcessor] Advanced Fusion Scoring (Historical + External) complete.")

        return [kw[0] for kw in scored_keywords]

    def generate_negative_keywords(self, inputs, context):
        """
        Generates a final list of negative keywords by combining research candidates
        with logical inferences based on product attributes.
        """
        logging.info("[KeywordProcessor] Generating final negative keyword list.")

        market_negatives = set(inputs.get('ads_seed_negative', []))
        proactive_candidates = set(inputs.get('proactive_negative_candidates', []))
        product_info = inputs.get('product_info', {})

        inferred_negatives = set()

        # Centralized logical inference based on material
        material = product_info.get('material', '').lower() if isinstance(product_info.get('material'), str) else ""
        karats = product_info.get('karats', [])

        if 'solid gold' in material or '14k' in karats or '18k' in karats:
            inferred_negatives.update(['gold plated', 'plated', 'gold filled', 'filled', 'vermeil', 'kaplama'])
            logging.info("Product is solid gold. Inferred negatives: 'plated', 'filled', 'vermeil', 'kaplama'.")

        if 'sterling silver' in material:
            inferred_negatives.update(['silver plated'])

        # Combine all sources and deduplicate
        final_negatives = list(market_negatives.union(proactive_candidates).union(inferred_negatives))
        logging.info(f"Final negative keyword list generated with {len(final_negatives)} terms.")

        return {"final_negative_keywords": final_negatives}

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution entry point. Dispatches to the correct method based on inputs.
        """
        # Check if this execution is for negative keyword generation (Task 2.2)
        if 'ads_seed_negative' in inputs or 'proactive_negative_candidates' in inputs:
            logging.info("[KeywordProcessor] Dispatching to negative keyword generation.")
            return self.generate_negative_keywords(inputs, context)

        # Fallback to the original keyword scoring workflow
        logging.info("[KeywordProcessor] Dispatching to standard keyword preparation.")
        seed = inputs.get("seed")
        if not seed:
            raise ValueError("Input 'seed' is required for the standard keyword processing workflow.")

        market_tags = inputs.get("market_tags", [])
        visual_tags = inputs.get("visual_tags", [])
        external_metrics = inputs.get("external_metrics", {})

        collected = self._collect(seed)
        filtered = self._filter(collected)
        merged = self._merge(filtered, market_tags, visual_tags)
        selected = self._score_and_select(merged, db_manager, external_metrics)

        output = {
            "coreKeywords": selected[:5],
            "longTailKeywords": selected[5:],
            "metrics": {"totalSearchVolume": len(selected) * 100, "competitorDensity": 0.6}
        }
        logging.info("[KeywordProcessor] Standard keyword preparation complete.")
        return output