import csv
import io
import json
from version_control import VersionControl

class Exporter:
    def __init__(self, config=None):
        # The main config is passed during execution
        self.config = config if config else {}

    def execute(self, inputs, context, knowledge_manager=None):
        """
        Exports the final product listing to a versioned CSV file with metadata.
        """
        # Load the primary configuration to get column order and versioning rules
        try:
            with open('project_core/finalv1.json', 'r', encoding='utf-8') as f:
                main_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {'status': 'FAIL', 'message': f'Could not load or parse project_core/finalv1.json: {e}', 'data': None}

        # The assembled listing data is expected from the previous step (listing_assembler)
        # It's a dictionary representing a single row.
        final_listing_data = inputs.get('assembled_listing')
        if not final_listing_data:
            return {'status': 'FAIL', 'message': 'No assembled listing data provided to exporter.', 'data': None}

        try:
            # Get column order from the main configuration
            export_columns = main_config.get('exp', {}).get('cols', [])
            if not export_columns:
                 return {'status': 'FAIL', 'message': "Export columns ('exp.cols') not found in config.", 'data': None}

            # --- Convert dictionary to CSV string in memory ---
            # Use io.StringIO to act like a file in memory
            string_buffer = io.StringIO()
            writer = csv.DictWriter(string_buffer, fieldnames=export_columns)

            # Write header
            writer.writeheader()

            # Filter the dictionary to include only the required columns before writing
            row_to_write = {col: final_listing_data.get(col, '') for col in export_columns}
            writer.writerow(row_to_write)

            # Get the CSV content as a string
            csv_string_data = string_buffer.getvalue()
            string_buffer.close()

            # --- Refactored File Writing Logic ---
            # Initialize VersionControl with the 'fs.ver' configuration
            versioning_config = main_config.get('fs', {}).get('ver', {})
            if not versioning_config:
                return {'status': 'FAIL', 'message': "Versioning configuration ('fs.ver') not found in config.", 'data': None}

            vc = VersionControl(versioning_config=versioning_config)

            # Save the CSV string data using the version controller
            save_result = vc.save_with_metadata(
                base_path='exports/etsy_listing_export.csv',
                data=csv_string_data,
                actor='exporter.py',
                reason='Exported final listing to CSV format for upload.'
            )

            # Return the path to the newly created versioned file
            return {'status': 'PASS', 'message': f'Listing exported successfully to {save_result.get("filepath")}', 'data': {'filepath': save_result.get('filepath')}}

        except Exception as e:
            import traceback
            print(f"Error during file export in Exporter: {traceback.format_exc()}")
            return {'status': 'FAIL', 'message': f'An error occurred during export: {str(e)}', 'data': None}