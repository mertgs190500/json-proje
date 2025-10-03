import json
import logging

class DescriptionGenerator:
    """
    Generates SEO-optimized product descriptions based on market analysis,
    product data, and predefined business rules.
    """

    def __init__(self):
        """
        Initializes the DescriptionGenerator by loading rules from the central JSON configuration.
        """
        self.rules = {}
        try:
            with open('project_core/finalv1.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Load structural guide for description sections
                self.rules['structure_guide'] = config.get('advisory_guides', {}).get('8', {})
                logging.info(f"Loaded structure guide: {self.rules['structure_guide']}")

                # Load validation rules from the specific step definition
                self.rules['validation_rules'] = config.get('s', {}).get('11', {}).get('c', {})
                logging.info(f"Loaded validation rules: {self.rules['validation_rules']}")
                
                # Load brand voice profile
                self.rules['brand_voice'] = config.get('shop_profile', {}).get('brand_voice', {})
                logging.info(f"Loaded brand voice: {self.rules['brand_voice']}")

                # Load general product/shop logistics info
                self.rules['logistics_info'] = config.get('product_record', {}).get('shop_logistics', {})
                self.rules['shop_profile_logistics'] = config.get('shop_profile', {})
                logging.info(f"Loaded logistics info: {self.rules['logistics_info']}")

            logging.info("DescriptionGenerator initialized successfully with rules from finalv1.json.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load or parse finalv1.json: {e}")
            # Initialize with empty rules to prevent crashes, which helps in isolated testing
            self.rules = {
                'structure_guide': {}, 'validation_rules': {}, 'brand_voice': {}, 'logistics_info': {}, 'shop_profile_logistics': {}
            }

    def execute(self, inputs, context, db_manager=None):
        """
        Orchestrates the description generation and validation process.
        """
        logging.info("DescriptionGenerator execution started.")

        market_data = inputs.get("market_analysis_results", {})
        final_title = inputs.get("title_final", "")
        product_data = inputs.get("product_data", {})
        if isinstance(product_data, list):
            product_data = product_data[0] if product_data else {}


        if not all([market_data, final_title, product_data]):
            logging.error("Missing critical inputs: market_analysis_results, title_final, or product_data.")
            return {"description_final": "Error: Missing critical inputs.", "validation_report": {}}

        description_parts = self._generate_description_sections(market_data, final_title, product_data)
        final_description = self._assemble_description(description_parts)
        validation_report = self._validate_description(final_description, market_data)

        logging.info("DescriptionGenerator execution finished.")

        return {
            "description_final": final_description,
            "validation_report": validation_report
        }

    def _generate_description_sections(self, market_data, final_title, product_data):
        """
        Generates each section of the description (Hook, Features, etc.)
        by calling specialized helper methods.
        """
        logging.info("Generating description sections...")
        
        hook = self._create_hook(final_title, market_data.get('focus_keywords', []))
        features = self._create_features_list(product_data)
        story = self._create_story_section()
        logistics = self._create_logistics_section()
        
        return {
            "hook": hook,
            "features": features,
            "story": story,
            "logistics": logistics,
        }

    def _create_hook(self, final_title, focus_keywords):
        """Creates the introductory hook, ensuring the focus keyword is in the first sentence."""
        brand_keywords = self.rules.get('brand_voice', {}).get('keywords', ['quality', 'timeless', 'elegant'])
        focus_keyword = focus_keywords[0] if focus_keywords else "unique jewelry"
        
        # Construct the hook to include the focus keyword in the first sentence.
        hook_text = f"Experience timeless elegance with our {focus_keyword}, the {final_title}. "
        hook_text += f"This exquisite piece is handcrafted to be a cherished treasure, perfect for those who appreciate {brand_keywords[0]} design."
        
        return hook_text[:160] # Adhere to the 160 character hook limit

    def _create_features_list(self, product_data):
        """Creates a bulleted list of product specifications."""
        features = []
        
        # Using .get() for safe key access from product_data
        if product_data.get('materials'):
            features.append(f"Material: {', '.join(product_data['materials'])}")
        if product_data.get('pricing'):
            karats = ', '.join(product_data['pricing'].keys())
            features.append(f"Karat: Available in {karats}")
        if self.rules.get('logistics_info', {}).get('olculer'):
            features.append(f"Size: {self.rules['logistics_info']['olculer']}")

        # Format as a bulleted list
        return "Product Details:\n" + "\n".join([f"• {item}" for item in features])

    def _create_story_section(self):
        """Creates a brief brand story aligned with the brand voice."""
        brand_voice = self.rules.get('brand_voice', {})
        tone = brand_voice.get('tone', 'elegant and professional')
        keywords = brand_voice.get('keywords', ['quality', 'timeless'])
        
        story = f"Our commitment to {keywords[1]} craftsmanship ensures every piece is a work of art. "
        story += f"We believe in creating {keywords[2]}, {tone.split(',')[0]} jewelry that you'll cherish for a lifetime."
        return story

    def _create_logistics_section(self):
        """Creates the logistics, shipping, and returns section from rules."""
        guide = self.rules.get('structure_guide', {})
        must_includes = guide.get('must_include_from_product_info', [])
        
        # The 'must_include_from_product_info' from finalv1.json is a list of ready-made strings.
        # We can directly use them.
        logistics_text = "\n".join(must_includes)
        
        # Add return policy from shop_profile
        logistics_text += "\n" + self.rules.get('logistics_info', {}).get('returns', {}).get('window_text', '15-day returns') + " return policy."
        
        return "Shipping & Policies:\n" + logistics_text

    def _assemble_description(self, parts):
        """
        Assembles the generated sections into a single formatted string.
        """
        logging.info("Assembling final description...")
        
        # Join sections with double newlines for clear separation
        full_description = (
            f"{parts['hook']}\n\n"
            f"{parts['features']}\n\n"
            f"{parts['story']}\n\n"
            f"{parts['logistics']}"
        )
        return full_description

    def _validate_description(self, description, market_data):
        """Validates the generated description against business rules from finalv1.json."""
        logging.info("Validating final description...")
        rules = self.rules.get('validation_rules', {})
        if not rules:
            logging.warning("No validation rules found in config.")
            return {"overall_status": "WARNING", "checks": [{"name": "Rules Loading", "status": "FAIL", "details": "No validation rules loaded."}]}

        report = {"overall_status": "PASS", "checks": []}

        # 1. Length Check
        min_len = rules.get('description_min_chars', 200)
        max_len = rules.get('description_max_chars', 3000)
        desc_len = len(description)
        length_pass = min_len <= desc_len <= max_len
        report['checks'].append({"name": "Length Check", "status": "PASS" if length_pass else "FAIL", "details": f"Length: {desc_len} (Min: {min_len}, Max: {max_len})"})
        if not length_pass: report['overall_status'] = "FAIL"

        # 2. Mandatory Content Check (Focus keyword in first sentence)
        focus_keyword = market_data.get('focus_keywords', [''])[0] if market_data.get('focus_keywords') else ''
        first_sentence = description.split('.')[0]
        keyword_pass = focus_keyword.lower() in first_sentence.lower() if focus_keyword else False
        report['checks'].append({"name": "Focus Keyword Check", "status": "PASS" if keyword_pass else "FAIL", "details": f"Focus keyword '{focus_keyword}' in first sentence."})
        if not keyword_pass: report['overall_status'] = "FAIL"
        
        # 3. Logistics Information Check
        guide = self.rules.get('structure_guide', {})
        must_includes = guide.get('must_include_from_product_info', [])
        missing_logistics = [item for item in must_includes if item not in description]
        logistics_pass = not missing_logistics
        report['checks'].append({"name": "Logistics Info Check", "status": "PASS" if logistics_pass else "FAIL", "details": f"Missing: {missing_logistics}" if missing_logistics else "All logistics info included."})
        if not logistics_pass: report['overall_status'] = "FAIL"

        # 4. Forbidden Words Check
        forbidden_terms = self.rules.get('validation_rules',{}).get('forbidden_terms_always', [])
        if isinstance(forbidden_terms, list):
            hits = [term for term in forbidden_terms if term.lower() in description.lower()]
            forbidden_pass = not hits
            report['checks'].append({"name": "Forbidden Words Check", "status": "PASS" if forbidden_pass else "FAIL", "details": f"Forbidden terms found: {hits}" if hits else "No forbidden terms found."})
            if not forbidden_pass: report['overall_status'] = "FAIL"
        else:
            report['checks'].append({"name": "Forbidden Words Check", "status": "WARNING", "details": "Could not parse forbidden_terms_always."})

        return report
