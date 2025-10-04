import json
import logging
from version_control import VersionControl

class ListingAssembler:
    def __init__(self, config=None):
        # The main config is passed during execution, this is for initialization
        self.config = config if config else {}
        self.logger = logging.getLogger(__name__)

    def execute(self, inputs, context, knowledge_manager=None):
        """
        Assembles the final product listing, suggests a registration type,
        and saves it as a versioned JSON file.
        """
        self.logger.info("[ListingAssembler] Assembly process started.")

        try:
            with open('project_core/finalv1.json', 'r', encoding='utf-8') as f:
                main_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Could not load or parse project_core/finalv1.json: {e}")
            return {'status': 'FAIL', 'message': f'Configuration error: {e}', 'data': None}

        # --- Data Assembly ---
        export_columns = main_config.get('exp', {}).get('cols', [])
        final_listing = {}

        # Safely get data from inputs and context
        product_data = inputs.get('product_data', {})
        final_listing['record_id'] = product_data.get('id', '')
        final_listing['op_type'] = 'CREATE'
        final_listing['is_deleted'] = 'false'
        final_listing['product.title'] = inputs.get('title_final', '')
        final_listing['product.description'] = inputs.get('description_final', '')
        final_listing['product.tags'] = ",".join(inputs.get('final_tags', []))

        pricing_info = product_data.get('pricing', {})
        final_listing['pricing.price_value'] = pricing_info.get('price', '')
        final_listing['pricing.price_currency'] = pricing_info.get('currency', 'USD')

        images = inputs.get('images', [])
        for i in range(5):
            col_name = f'image_{i+1}'
            final_listing[col_name] = images[i] if i < len(images) else ''

        for col in export_columns:
            if col not in final_listing:
                final_listing[col] = ''

        # --- Automatic Registration Type Suggestion (Task 3.3) ---
        self.logger.info("Generating registration type suggestion...")
        compliance_status = inputs.get('compliance_status', 'FAIL')
        seo_score = inputs.get('seo_score', 0)
        qa_warnings_count = len(inputs.get('qa_warnings', []))

        suggestion = 'draft' # Default suggestion
        if compliance_status == 'PASS' and seo_score > 80 and qa_warnings_count == 0:
            suggestion = 'publish'
            self.logger.info("Suggestion: 'publish' (All checks passed, high SEO score).")
        else:
            self.logger.warning(f"Suggestion: 'draft'. Reasons: Compliance={compliance_status}, SEO Score={seo_score}, QA Warnings={qa_warnings_count}")

        # --- Save Output ---
        try:
            versioning_config = main_config.get('fs', {}).get('ver', {})
            if not versioning_config:
                raise ValueError("Versioning configuration ('fs.ver') not found in config.")

            vc = VersionControl(versioning_config=versioning_config)
            save_result = vc.save_with_metadata(
                base_path='outputs/assembled_listing.json',
                data=final_listing,
                actor='listing_assembler.py',
                reason='Assembled final listing from all SEO components.'
            )

            output_data = {
                'assembled_listing': final_listing,
                'filepath': save_result.get('filepath'),
                'listing.registration_suggestion': suggestion
            }

            self.logger.info("Listing assembled and saved successfully.")
            return {'status': 'PASS', 'message': 'Listing assembled successfully.', 'data': output_data}

        except Exception as e:
            self.logger.error(f"Error during file saving in ListingAssembler: {e}", exc_info=True)
            return {'status': 'FAIL', 'message': f'An error occurred while saving the listing: {str(e)}', 'data': None}
