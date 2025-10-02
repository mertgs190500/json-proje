import logging

class PackagingStrategist:
    def execute(self, inputs, context, db_manager=None):
        """
        Optimizes listing attributes and creates Etsy Ads keyword strategies.
        """
        logging.info("[PackagingStrategist] Strategic packaging initiated.")

        # Get inputs resolved by the orchestrator
        seo_content = inputs.get("seo_content", {})
        visual_data = inputs.get("visual_data", {})
        keyword_data = inputs.get("keyword_data", {})
        performance_metrics = inputs.get("performance_metrics", {})

        # 1. Optimize Attributes
        attributes = self._optimize_attributes(visual_data, seo_content)

        # 2. Generate Etsy Ads Lists
        ads_strategy = self._generate_ads_lists(keyword_data, performance_metrics)

        # The output must conform to the StrategicPackagingData contract
        output = {
            "attributes": attributes,
            "ads_strategy": ads_strategy
        }
        logging.info("[PackagingStrategist] Packaging complete.")
        return output

    def _optimize_attributes(self, visual_data, seo_content):
        """Selects listing attributes based on visual and textual content."""
        attrs = {}
        # Use data from visual analysis (Report 2.3.1)
        if visual_data.get("detected_colors"):
            attrs["primary_color"] = visual_data["detected_colors"][0]
        if visual_data.get("detected_materials"):
            attrs["material"] = visual_data["detected_materials"][0]

        # Infer attributes from text content
        all_text = (seo_content.get("title", "") + " " + " ".join(seo_content.get("tags", []))).lower()

        # Simple rule-based detection (can be expanded)
        if "minimalist" in all_text or "modern" in all_text:
            attrs["style"] = "Minimalist/Modern"
        if "gift" in all_text or "birthday" in all_text:
            attrs["occasion"] = "Birthday/Gift"

        logging.info(f"  > Optimized Attributes: {attrs}")
        return attrs

    def _generate_ads_lists(self, keyword_data, metrics):
        """Generates positive and negative keyword lists based on performance metrics."""
        # This strategy uses thresholds, which could be made configurable via inputs.
        CR_HIGH = 0.04  # High Conversion Rate threshold (e.g., 4%)
        CR_LOW = 0.01   # Low Conversion Rate threshold (e.g., 1%)

        positive = []
        negative = []

        all_keywords = keyword_data.get("coreKeywords", []) + keyword_data.get("longTailKeywords", [])

        for keyword in all_keywords:
            # Get the conversion rate for the keyword, default to an average of 2% if not present
            cr = metrics.get(keyword, {}).get("conversion_rate", 0.02)

            if cr >= CR_HIGH:
                positive.append(keyword)
            elif cr < CR_LOW:
                # Low CR keywords are risky for ad spend, add to negative list
                negative.append(keyword)

        logging.info(f"  > Ads Strategy: {len(positive)} positive, {len(negative)} negative keywords.")
        return {
            "positive_priority_keywords": positive,
            "negative_keywords": negative
        }