import json

class ListingAssembler:
    def __init__(self, config):
        self.config = config

    def execute(self, inputs, context, db_manager=None):
        """
        Assembles the final product listing from various generated parts.
        """
        compliance_report = context.get('compliance_report', {})
        if compliance_report.get('status') != 'PASS':
            return {'status': 'FAIL', 'message': 'Compliance check did not pass. Halting assembly.', 'data': None}

        # Get the required columns from the configuration
        export_columns = self.config.get('exp', {}).get('cols', [])

        final_listing = {}

        # Populate the final listing dictionary based on the defined columns
        # This is a simplified mapping. A real implementation would have more robust logic.
        final_listing['record_id'] = context.get('product_data', {}).get('id', '')
        final_listing['op_type'] = 'CREATE'
        final_listing['is_deleted'] = 'false'
        final_listing['product.title'] = context.get('title', '')
        final_listing['product.description'] = context.get('description', '')
        final_listing['product.tags'] = ",".join(context.get('tags', []))

        # Example for pricing - assuming it's in product_data
        pricing_info = context.get('product_data', {}).get('pricing', {})
        final_listing['pricing.price_value'] = pricing_info.get('price', '')
        final_listing['pricing.price_currency'] = pricing_info.get('currency', 'USD')

        # Example for images - assuming they are in context
        images = context.get('images', [])
        for i in range(5):
            col_name = f'image_{i+1}'
            if i < len(images):
                final_listing[col_name] = images[i]
            else:
                final_listing[col_name] = ''

        # Ensure all columns are present, fill with empty strings if not
        for col in export_columns:
            if col not in final_listing:
                final_listing[col] = ''

        return {'status': 'PASS', 'message': 'Listing assembled successfully.', 'data': final_listing}