import logging
import re
import json
from version_control import VersionControl

class TitleOptimizer:
    def __init__(self):
        """
        Initializes the TitleOptimizer with predefined business rules.
        """
        # Rule: Maximum title length
        self.MAX_LENGTH = 140
        # Rule: "Front-loading" - critical keywords in the first 40 characters
        self.FRONT_LOAD_CUTOFF = 40
        # Rule: Forbidden terms that must not appear in the title
        self.FORBIDDEN_TERMS = ["iade", "return"]
        # Rule: Word repetition limit
        self.MAX_WORD_REPETITION = 2
        logging.info("TitleOptimizer initialized with business rules.")

        # Load configuration for VersionControl
        try:
            with open("project_core/finalv1.json", 'r') as f:
                config = json.load(f)
            versioning_config = config.get("fs", {}).get("ver", {})
            if not versioning_config:
                raise ValueError("Versioning configuration 'fs.ver' not found in finalv1.json")
            self.vc = VersionControl(versioning_config=versioning_config)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to initialize VersionControl: {e}")
            self.vc = None


    def execute(self, inputs, context, db_manager=None):
        """
        Orchestrates the title generation, validation, and selection process.

        Args:
            inputs (dict): A dictionary containing 'market_analysis' and 'product_data'.
                           - 'market_analysis': Expected to have 'focus_keywords' and 'secondary_keywords'.
                           - 'product_data': Expected to have 'material', 'karat', 'color', etc.
            context (dict): The workflow context (not used in this version).
            db_manager (DBManager): The database manager (not used in this version).

        Returns:
            dict: A dictionary containing the final optimized title and variations.
                  e.g., {'title_final': '...', 'title_variations': [...]}
        """
        logging.info("TitleOptimizer execution started.")

        market_analysis = inputs.get("market_analysis", {})
        product_data = inputs.get("product_data", {})
        visual_attributes = inputs.get("visual_attribute_suggestions", [])

        if not market_analysis.get("focus_keywords"):
            logging.error("Missing 'focus_keywords' in market_analysis input.")
            return {"title_final": "Error: Missing focus keywords", "title_variations": []}

        if not all(k in product_data for k in ['material', 'pricing', 'colors']):
            logging.error("Missing critical keys like 'material', 'pricing', or 'colors' in product_data input.")
            return {"title_final": "Error: Incomplete product data", "title_variations": []}

        # 1. Generate title variations
        all_titles = self._generate_variations(market_analysis, product_data)
        if not all_titles:
            logging.warning("No title variations could be generated.")
            return {"title_final": "Error: Could not generate titles", "title_variations": []}

        # 2. Validate and score each title
        scored_titles = self._validate_and_score(all_titles, market_analysis, product_data, visual_attributes)

        # 3. Select the best title
        best_title, selection_log = self._select_best_title(scored_titles)
        if not best_title:
            logging.error("No titles passed validation.")
            return {"title_final": "Error: No valid titles found", "title_variations": all_titles}

        logging.info(selection_log)

        output_data = {
            "title_final": best_title,
            "title_variations": all_titles
        }

        if self.vc:
            try:
                save_result = self.vc.save_with_metadata(
                    base_path='outputs/optimized_title.json',
                    data=output_data,
                    actor='title_optimizer.py',
                    reason='Generated optimized SEO title.'
                )
                logging.info(f"Successfully saved optimized title to {save_result.get('filepath')}")
            except Exception as e:
                logging.error(f"Failed to save optimized title using VersionControl: {e}")

        logging.info("TitleOptimizer execution finished.")
        return output_data

    def _generate_variations(self, market_analysis, product_data):
        """
        Generates a list of title variations using templates, keywords, and product data.
        This version is designed to create titles that are more likely to pass validation.
        """
        logging.info("Generating title variations.")
        focus_keywords = market_analysis.get("focus_keywords", [])
        if not focus_keywords:
            return []

        # Extract product details
        color = product_data.get("colors", [""])[0]
        karat = list(product_data.get("pricing", {}).keys())[0] if product_data.get("pricing") else ""

        variations = []
        primary_keyword = focus_keywords[0]

        # 1. Primary Title: Main keyword + essential info
        # Example: "Dainty Gold Ring | 10K Yellow Gold Band"
        title1 = f"{primary_keyword} | {karat} {color} Band"
        variations.append(title1)

        # 2. Alternative Title: Secondary keyword + gift angle
        if len(focus_keywords) > 1:
            secondary_keyword = focus_keywords[1]
            # Example: "Stacking Ring - 10K Yellow Gold - Perfect Gift for Her"
            title2 = f"{secondary_keyword} - {karat} {color} - Perfect Gift for Her"
            variations.append(title2)

        # 3. Alternative Title: Benefit-oriented
        # Example: "Handmade Dainty Gold Ring for Anniversary | 10K Yellow Gold"
        title3 = f"Handmade {primary_keyword} for Anniversary | {karat} {color}"
        variations.append(title3)

        logging.info(f"Generated {len(variations)} compliant title variations.")
        return variations

    def _validate_and_score(self, titles, market_analysis, product_data, visual_attributes=None):
        """
        Validates a list of titles against all business rules and assigns a score.
        A score of 0 means the title is invalid.
        """
        logging.info("Validating and scoring titles.")
        if visual_attributes is None:
            visual_attributes = []
        scored_titles = []
        primary_keyword = market_analysis.get("focus_keywords", [""])[0]

        for title in titles:
            score = 100  # Base score for any generated title

            # Run all validation checks. If any check returns False, the score is invalidated.
            if not self._check_length(title):
                score = 0
            if not self._check_no_forbidden_terms(title):
                score = 0
            if not self._check_word_repetition(title):
                score = 0
            if not self._check_mandatory_content(title, product_data):
                score = 0

            # Scoring adjustments for valid titles
            if score > 0:
                if self._check_front_loading(title, primary_keyword):
                    score += 20  # Bonus for good SEO practice
                else:
                    score -= 10 # Penalty

                if self._check_visual_consistency(title, visual_attributes):
                    score += 15 # Bonus for visual consistency
                else:
                    score -= 15 # Penalty for inconsistency

            scored_titles.append((title, score))
        return scored_titles

    def _select_best_title(self, scored_titles):
        """
        Selects the best title from a list of scored titles.
        Filters out invalid titles (score=0) and picks the one with the highest score.
        """
        logging.info("Selecting best title.")
        valid_titles = [item for item in scored_titles if item[1] > 0]

        if not valid_titles:
            return None, "No titles passed the validation checks."

        # Sort by score (descending)
        valid_titles.sort(key=lambda x: x[1], reverse=True)

        best_title, best_score = valid_titles[0]
        log = f"Selected '{best_title}' (Score: {best_score}) as the best title. Total valid options: {len(valid_titles)}."
        return best_title, log

    # --- Validation Helper Methods ---

    def _check_length(self, title):
        is_valid = len(title) <= self.MAX_LENGTH
        if not is_valid:
            logging.warning(f"Validation FAIL (Length): '{title}' ({len(title)} > {self.MAX_LENGTH})")
        return is_valid

    def _check_front_loading(self, title, keyword):
        is_valid = keyword.lower() in title[:self.FRONT_LOAD_CUTOFF].lower()
        if not is_valid:
            logging.warning(f"Validation WARN (Front-load): Keyword '{keyword}' not in first {self.FRONT_LOAD_CUTOFF} chars of '{title}'")
        return is_valid

    def _check_no_forbidden_terms(self, title):
        for term in self.FORBIDDEN_TERMS:
            if term.lower() in title.lower():
                logging.warning(f"Validation FAIL (Forbidden): Term '{term}' found in '{title}'")
                return False
        return True

    def _check_word_repetition(self, title):
        words = re.findall(r'\w+', title.lower())
        for word in words:
            if words.count(word) > self.MAX_WORD_REPETITION:
                logging.warning(f"Validation FAIL (Repetition): Word '{word}' repeated more than {self.MAX_WORD_REPETITION} times in '{title}'")
                return False
        return True

    def _check_mandatory_content(self, title, product_data):
        """Checks if essential product attributes (karat, color) are in the title."""
        karats = list(product_data.get("pricing", {}).keys())
        colors = product_data.get("colors", [])

        # Check for at least one karat and one color
        has_karat = any(k.lower() in title.lower() for k in karats)
        has_color = any(c.lower() in title.lower() for c in colors)

        if not (has_karat and has_color):
            logging.warning(f"Validation FAIL (Mandatory): Missing karat or color in '{title}'")
            return False
        return True

    def _check_visual_consistency(self, title, visual_attributes):
        """Checks if at least one visual attribute is present in the title."""
        if not visual_attributes:
            return True # No attributes to check against, so it passes by default.

        is_consistent = any(attr.lower() in title.lower() for attr in visual_attributes)
        if not is_consistent:
            logging.warning(f"Validation WARN (Visual Consistency): No visual attributes {visual_attributes} found in title '{title}'")
        return is_consistent