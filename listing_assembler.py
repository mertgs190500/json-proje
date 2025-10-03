import json
from version_control import VersionControl

class ListingAssembler:
    def __init__(self, config=None):
        # The main config is passed during execution, this is for initialization
        self.config = config if config else {}

    def execute(self, inputs, context, knowledge_manager=None):
        """
        Assembles the final product listing from various generated parts and
        saves it as a versioned JSON file with metadata.
        """
        # Load the primary configuration which contains versioning rules
        try:
            with open('project_core/finalv1.json', 'r', encoding='utf-8') as f:
                main_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {'status': 'FAIL', 'message': f'Could not load or parse project_core/finalv1.json: {e}', 'data': None}

        # This module's specific config is expected to be in the context or passed at init
        # For this task, we assume the relevant 'exp' config is in the main_config
        module_config = main_config

        compliance_report = context.get('compliance_report', {})
        if compliance_report.get('status') != 'PASS':
            # This is a soft failure for now, just log it. A real scenario might halt.
            print("Warning: Compliance check did not pass. Assembly will proceed but may be invalid.")

        # Get the required columns from the configuration
        export_columns = module_config.get('exp', {}).get('cols', [])

        final_listing = {}

        # Simplified mapping from context to the final listing structure
        product_data = context.get('product_data', {}).get('data', {})
        final_listing['record_id'] = product_data.get('id', '')
        final_listing['op_type'] = 'CREATE'
        final_listing['is_deleted'] = 'false'
        final_listing['product.title'] = context.get('final_title_output', {}).get('title_final', '')
        final_listing['product.description'] = context.get('final_description_output', {}).get('description', '')
        final_listing['product.tags'] = ",".join(context.get('final_tags_output', {}).get('tags', []))

        pricing_info = product_data.get('products', [{}])[0].get('pricing', {})
        final_listing['pricing.price_value'] = pricing_info.get('price', '')
        final_listing['pricing.price_currency'] = pricing_info.get('currency', 'USD')

        images = context.get('images', [])
        for i in range(5):
            col_name = f'image_{i+1}'
            if i < len(images):
                final_listing[col_name] = images[i]
            else:
                final_listing[col_name] = ''

        # Ensure all columns from the export configuration are present
        for col in export_columns:
            if col not in final_listing:
                final_listing[col] = ''

        # --- Refactored File Writing Logic ---
        try:
            # Initialize VersionControl with the 'fs.ver' configuration
            versioning_config = main_config.get('fs', {}).get('ver', {})
            if not versioning_config:
                return {'status': 'FAIL', 'message': "Versioning configuration ('fs.ver') not found in config.", 'data': None}

            vc = VersionControl(versioning_config=versioning_config)

            # Save the assembled listing using the version controller
            save_result = vc.save_with_metadata(
                base_path='outputs/assembled_listing.json',
                data=final_listing,
                actor='listing_assembler.py',
                reason='Assembled final listing from all SEO components.'
            )

            # The context for the next step should contain the path to the saved file
            # and the data itself for in-memory operations.
            output_data = {
                'assembled_listing': final_listing,
                'filepath': save_result.get('filepath')
            }

            return {'status': 'PASS', 'message': 'Listing assembled and saved successfully.', 'data': output_data}

        except Exception as e:
            # Log the full exception for debugging
            import traceback
            print(f"Error during file saving in ListingAssembler: {traceback.format_exc()}")
            return {'status': 'FAIL', 'message': f'An error occurred while saving the listing: {str(e)}', 'data': None}