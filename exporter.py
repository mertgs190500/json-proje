import logging
import json
import csv
import os
from version_control import VersionControl

class Exporter:
    """
    Exports the final assembled listing object to one or more file formats,
    utilizing the VersionControl module to prevent overwrites.
    """

    def __init__(self):
        # Initialize the version controller. Policy could be passed via inputs if needed.
        self.vc = VersionControl()

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution method. Saves the listing object to disk in the specified formats.
        """
        logging.info("[Exporter] Starting versioned export process.")

        listing_object = inputs.get("listing_object")
        formats = inputs.get("formats", ["json"])
        output_path_base = inputs.get("output_path_base", "output/listing")

        if not listing_object:
            logging.error("[Exporter] No listing object provided to export.")
            return {"exported_files": {}}

        exported_files = {}

        for fmt in formats:
            # The base path for versioning will be like 'output/listing.json'
            version_base_path = f"{output_path_base}.{fmt}"

            # Prepare data based on format
            data_to_save = listing_object
            if fmt.lower() == "csv":
                # For CSV, we save the flattened dictionary as a string
                flat_data = self._flatten_dict(listing_object)
                # This is a simplified representation for CSV saving via version_control
                # In a real scenario, the version_control module would need to handle CSV writing.
                data_to_save = self._dict_to_csv_string(flat_data)

            # Use the version controller to save the file
            new_filepath = self.vc.save_new_version(version_base_path, data_to_save)

            if new_filepath:
                exported_files[fmt] = new_filepath

        logging.info(f"[Exporter] Export complete. Files created: {list(exported_files.values())}")
        return {"exported_files": exported_files}

    def _dict_to_csv_string(self, data_dict):
        """Converts a dictionary to a CSV string (header + 1 row)."""
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data_dict.keys())
        writer.writeheader()
        writer.writerow(data_dict)
        return output.getvalue()

    def _flatten_dict(self, d, parent_key='', sep='_'):
        """
        Flattens a nested dictionary for CSV export.
        e.g., {'a': {'b': 1}} -> {'a_b': 1}
        """
        items = {}
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep=sep))
            elif isinstance(v, list):
                # Convert lists to a string to fit in a single CSV cell
                items[new_key] = ", ".join(map(str, v))
            else:
                items[new_key] = v
        return items