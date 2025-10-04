import logging
import re
from collections import Counter
from version_control import VersionControl

class TagGenerator:
    """
    Generates and selects the optimal 13 SEO tags based on a comprehensive analysis of
    market data, product information, and final SEO content (title, description).
    The logic adheres to rules specified in the project's configuration, such as
    character limits, forbidden terms, and diversity requirements.
    """

    def __init__(self):
        # Rules derived from finalv1.json analysis (/s/12/forbidden, etc.)
        self.FORBIDDEN_TERMS = {'turkey', 'gift idea', 'free shipping', 'sale', 'discount'}
        self.TAG_LENGTH_LIMIT = 20
        self.FINAL_TAG_COUNT = 13

    def _extract_terms(self, text, min_len=3):
        """Extracts unique, lowercased words from a text string."""
        if not isinstance(text, str):
            return set()
        words = re.findall(r'\b\w+\b', text.lower())
        return {word for word in words if len(word) >= min_len}

    def _get_root_word(self, phrase):
        """
        Gets a representative root for a phrase for deduplication purposes.
        This is a simple implementation; a more advanced version would use stemming/lemmatization.
        """
        words = phrase.lower().split()
        stemmed_words = []
        for word in words:
            # Simple stemmer: remove 's' unless it's 'ss' to handle simple plurals.
            if len(word) > 2 and word.endswith('s') and not word.endswith('ss'):
                stemmed_words.append(word[:-1])
            else:
                stemmed_words.append(word)
        
        # Sort the stemmed words to make the root order-independent
        return ' '.join(sorted(stemmed_words))

    def execute(self, inputs, context, knowledge_manager=None):
        """
        Main execution method called by the orchestrator.

        Args:
            inputs (dict): A dictionary containing all necessary data pools:
                           - 'market_analysis': Output from MarketAnalyzer.
                           - 'keyword_data': Focused keywords from KeywordProcessor.
                           - 'title_data': Output from TitleOptimizer.
                           - 'description_data': Output from DescriptionGenerator.
                           - 'product_attributes': A dictionary of product attributes.

        Returns:
            dict: A dictionary containing the 'final_tags' list.
        """
        logging.info("[TagGenerator] Starting tag generation process.")

        # 1. --- Data Aggregation ---
        # Collect keywords from all relevant sources into a single weighted list.
        candidate_pool = []
        
        # From market analysis
        market_analysis = inputs.get('market_analysis', {})
        our_tag_pool = set() # Using a set for efficient lookup

        popular_keywords = market_analysis.get('popular_keywords_top', [])
        candidate_pool.extend(popular_keywords * 3) # Higher weight
        our_tag_pool.update(popular_keywords)

        main_themes = market_analysis.get('competitor_signals', {}).get('main_themes', [])
        candidate_pool.extend(main_themes)
        our_tag_pool.update(main_themes)

        keyword_gaps = market_analysis.get('market_snapshot', {}).get('keyword_gaps', [])
        candidate_pool.extend(keyword_gaps)
        our_tag_pool.update(keyword_gaps)


        # From keyword processing
        keyword_data = inputs.get('keyword_data', {})
        focus_keywords = keyword_data.get('focus_keywords', [])
        supporting_keywords = keyword_data.get('supporting_keywords', [])
        our_tag_pool.update(focus_keywords)
        our_tag_pool.update(supporting_keywords)
        candidate_pool.extend(keyword_data.get('focus_keywords', []) * 5) # Highest weight
        candidate_pool.extend(keyword_data.get('supporting_keywords', []) * 2)

        # From final content
        title_data = inputs.get('title_data', {})
        final_title = title_data.get('final_title', '')
        title_terms = self._extract_terms(final_title)
        candidate_pool.extend(list(title_terms) * 3)

        description_data = inputs.get('description_data', {})
        final_description = description_data.get('final_description', '')
        description_terms = self._extract_terms(final_description)
        our_tag_pool.update(description_terms)
        candidate_pool.extend(list(description_terms))

        # --- Gap Analysis ---
        competitor_data = inputs.get('competitor_tags_data', {})
        if competitor_data and 'data' in competitor_data:
            competitor_tags = set()
            for item in competitor_data['data']:
                tags = item.get('Tags', '')
                if isinstance(tags, str):
                    # Assuming tags are comma-separated
                    competitor_tags.update([tag.strip().lower() for tag in tags.split(',')])

            opportunity_tags = competitor_tags - our_tag_pool
            logging.info(f"Found {len(opportunity_tags)} opportunity tags (gaps).")
            # Give opportunity tags a very high weight
            candidate_pool.extend(list(opportunity_tags) * 5)

        if not candidate_pool:
            logging.warning("[TagGenerator] Candidate pool is empty. Cannot generate tags.")
            return {"final_tags": []}

        # 2. --- Filtering and Cleaning ---
        logging.info(f"Initial candidate pool size: {len(candidate_pool)}")
        
        # Get product attributes for deduplication
        product_attributes = inputs.get('product_attributes', {})
        attribute_values = {str(v).lower() for v in product_attributes.values() if isinstance(v, str)}

        cleaned_candidates = []
        for tag in candidate_pool:
            tag_lower = tag.lower().strip()

            # Rule: Character length limit (<= 20)
            if len(tag_lower) > self.TAG_LENGTH_LIMIT:
                continue
            
            # Rule: Forbid specific terms
            if any(term in tag_lower for term in self.FORBIDDEN_TERMS):
                continue
                
            # Rule: Filter out single-word tags (prioritize multi-word)
            if ' ' not in tag_lower:
                continue

            # Rule: Deduplicate against product attributes
            if tag_lower in attribute_values:
                continue

            cleaned_candidates.append(tag_lower)
            
        logging.info(f"Pool size after cleaning and filtering: {len(cleaned_candidates)}")

        # 3. --- Scoring & Ranking ---
        # The scoring formula from /pl/scoring is simulated here by frequency,
        # which acts as a proxy for relevance and market usage.
        tag_counts = Counter(cleaned_candidates)
        # Sort by frequency (score) in descending order
        sorted_tags = [tag for tag, count in tag_counts.most_common()]

        # 4. --- Diversity and Final Selection ---
        final_tags = []
        used_root_words = set()

        for tag in sorted_tags:
            if len(final_tags) >= self.FINAL_TAG_COUNT:
                break

            root = self._get_root_word(tag)
            # Rule: Ensure no root word is repeated
            if root not in used_root_words:
                final_tags.append(tag)
                used_root_words.add(root)
        
        # If we still don't have 13 tags, we can backfill with single-word tags if necessary
        # (This part is an enhancement to ensure we always return 13 tags if possible)
        if len(final_tags) < self.FINAL_TAG_COUNT:
            single_word_candidates = [t.lower().strip() for t in candidate_pool if ' ' not in t.lower().strip()]
            single_word_counts = Counter(single_word_candidates)
            sorted_singles = [tag for tag, count in single_word_counts.most_common()]
            
            for tag in sorted_singles:
                if len(final_tags) >= self.FINAL_TAG_COUNT:
                    break
                root = self._get_root_word(tag)
                if root not in used_root_words and len(tag) <= self.TAG_LENGTH_LIMIT:
                    final_tags.append(tag)
                    used_root_words.add(root)

        final_tags_list = final_tags[:self.FINAL_TAG_COUNT]
        logging.info(f"[TagGenerator] Successfully generated {len(final_tags_list)} final tags.")

        output_data = {"final_tags": final_tags_list}

        # Save the output using VersionControl
        if isinstance(knowledge_manager, VersionControl):
            try:
                knowledge_manager.save_with_metadata(
                    base_path='outputs/generated_tags.json',
                    data=output_data,
                    actor='tag_generator.py',
                    reason='Generated 13 SEO tags based on analysis.'
                )
                logging.info("[TagGenerator] Successfully saved tags with metadata.")
            except Exception as e:
                # Log the error but don't crash the workflow
                logging.error(f"[TagGenerator] Failed to save tags using version control: {e}", exc_info=True)

        return output_data
