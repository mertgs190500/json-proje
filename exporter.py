import csv
import os
from datetime import datetime

class Exporter:
    def __init__(self, config):
        self.config = config

    def execute(self, inputs, context, db_manager=None):
        """
        Exports the final product listing to a CSV file.
        """
        final_listing = inputs.get('assembled_listing')
        if not final_listing:
            return {'status': 'FAIL', 'message': 'No assembled listing provided to exporter.', 'data': None}

        try:
            # Generate the filename
            naming_pattern = self.config.get('exp', {}).get('naming', {}).get('pattern', 'PRODUCT_EXPORT_%Y%m%d_%H%M%S_v1.csv')
            # A simple versioning mechanism, would need to be more robust in a real scenario
            version = 1
            filename = datetime.now().strftime(naming_pattern.format(N=version))

            output_dir = 'output/fs/export'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            filepath = os.path.join(output_dir, filename)

            # Get column order from config
            export_columns = self.config.get('exp', {}).get('cols', [])

            # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=export_columns)
                writer.writeheader()
                # Ensure only the specified columns are written, in the correct order
                row_to_write = {col: final_listing.get(col, '') for col in export_columns}
                writer.writerow(row_to_write)

            return {'status': 'PASS', 'message': f'Listing exported successfully to {filepath}', 'data': {'filepath': filepath}}

        except Exception as e:
            return {'status': 'FAIL', 'message': f'An error occurred during export: {str(e)}', 'data': None}