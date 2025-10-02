import logging
from collections import Counter

class TagGenerator:
    """
    Analyzes keyword pools from various sources to select the optimal 13 SEO tags
    based on a defined strategy and rules.
    """

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution method called by the orchestrator.

        Args:
            inputs (dict): A dictionary containing 'keyword_pools', 'product_attributes',
                           and 'final_title'.

        Returns:
            dict: A dictionary containing the 'final_tags' list.
        """
        logging.info("[TagGenerator] Starting tag generation.")

        keyword_pools = inputs.get("keyword_pools", {})
        product_attributes = inputs.get("product_attributes", {})
        final_title = inputs.get("final_title", "")

        # The core logic for selecting the best tags
        final_tags = self._select_best_tags(keyword_pools, product_attributes, final_title)

        logging.info(f"[TagGenerator] Generated {len(final_tags)} final tags.")
        return {"final_tags": final_tags}

    def _get_root_word(self, word):
        """
        A simple function to get the 'root' of a word for deduplication.
        (e.g., 'rings', 'ringing' -> 'ring'). This can be improved with stemming libraries.
        """
        word = word.lower()
        # A very basic approach
        for suffix in ['s', 'es', 'ing', 'ed']:
            if word.endswith(suffix):
                return word[:-len(suffix)]
        return word

    def _select_best_tags(self, pools, attributes, title):
        """
        Selects the top 13 tags based on source priority, uniqueness, and variety.
        This simulates the logic from /s/12/rs and /run/s/12/c.
        """

        # 1. Gather all potential tags from different sources
        # The order here defines the priority (source mix)
        potential_tags = []
        potential_tags.extend(pools.get("core_keywords", []))
        potential_tags.extend(pools.get("long_tail_keywords", []))

        # Add tags from product attributes (e.g., color, material)
        for key, value in attributes.items():
            if isinstance(value, str):
                potential_tags.append(value)
            elif isinstance(value, list):
                potential_tags.extend(value)

        # Add important words from the title
        potential_tags.extend(title.split())

        # 2. Clean and score tags
        # For this simulation, we'll just count frequency, but this could be more complex.
        # We also filter out very short words (e.g., 'a', 'an', 'in')
        cleaned_tags = [tag.lower().strip() for tag in potential_tags if len(tag) > 2]
        tag_counts = Counter(cleaned_tags)

        # 3. Select the final 13 tags
        final_tags = []
        used_root_words = set()

        # Sort by frequency (as a proxy for importance/relevance)
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        for tag, count in sorted_tags:
            if len(final_tags) >= 13:
                break

            root_word = self._get_root_word(tag)
            # Rule: Avoid repeating root words
            if root_word not in used_root_words:
                # Rule: Ensure tags fit within Etsy's 20-character limit
                if len(tag) <= 20:
                    final_tags.append(tag)
                    used_root_words.add(root_word)

        return final_tags