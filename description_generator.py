import logging

class DescriptionGenerator:
    """
    Generates an SEO-optimized and brand-compliant product description
    based on a set of rules and inputs.
    """

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution method called by the orchestrator.

        Args:
            inputs (dict): A dictionary containing all necessary data points like
                           'final_title', 'focus_keywords', 'product_data', 'shop_policies'.

        Returns:
            dict: A dictionary containing the 'formatted_description'.
        """
        logging.info("[DescriptionGenerator] Starting description generation.")

        final_title = inputs.get("final_title", "Our Awesome Product")
        focus_keywords = inputs.get("focus_keywords", [])
        product_data = inputs.get("product_data", {})
        shop_policies = inputs.get("shop_policies", {})
        brand_voice = inputs.get("brand_voice", "friendly") # e.g., 'friendly', 'formal'

        # Delegate to the generation logic
        description = self._generate_structured_description(
            final_title, focus_keywords, product_data, shop_policies, brand_voice
        )

        logging.info("[DescriptionGenerator] Description generation complete.")
        return {"formatted_description": description}

    def _generate_structured_description(self, title, keywords, product, policies, voice):
        """
        Constructs the description from various blocks, simulating a template engine.
        """

        # --- 1. Introduction Block ---
        # Use brand voice to alter the intro
        if voice == "friendly":
            intro = f"✨ Discover the charm of our {title}! ✨\nPerfect for {keywords[0] if keywords else 'any occasion'}, this piece is crafted with passion."
        else:
            intro = f"We are pleased to present the {title}.\nThis item is an excellent choice for individuals interested in {keywords[0] if keywords else 'high-quality crafts'}."

        # --- 2. Features Block ---
        material = product.get('material', 'high-quality materials')
        sizes = product.get('sizes_us', 'various sizes')
        features_list = [
            f"- Material: Crafted from premium {material}.",
            f"- Sizes: Available in a range of sizes ({sizes}).",
            f"- Keywords: {', '.join(keywords)}"
        ]
        features_block = "\n\n--- Product Details ---\n" + "\n".join(features_list)

        # --- 3. Policies Block ---
        shipping_policy = policies.get("shipping_info", "Contact us for shipping details.")
        return_policy = policies.get("return_info", "Contact us for returns.")
        policies_block = f"\n\n--- Our Promise ---\n🚚 {shipping_policy}\n↩️ {return_policy}"

        # --- 4. Assembly ---
        full_description = intro + features_block + policies_block

        return full_description.strip()