import logging
import pandas as pd

class CSVIngestor:
    def execute(self, inputs, context, db_manager=None):
        """
        Ingests data from a CSV file based on a given profile.
        """
        logging.info("[CSVIngestor] Executing CSV ingestion.")

        # Inputs should contain 'filepath' and 'profile'
        filepath = inputs.get("filepath")
        profile = inputs.get("profile") # This profile is already resolved by the orchestrator

        if not filepath or not profile:
            logging.error("[CSVIngestor] Missing 'filepath' or 'profile' in inputs.")
            return {"status": "error", "message": "Filepath or profile is missing."}

        try:
            # Use pandas to read CSV with parameters from the profile
            data = pd.read_csv(
                filepath,
                delimiter=profile.get("delimiter", ","),
                encoding=profile.get("encoding", "utf-8"),
                header=profile.get("header_row", 0)
            )

            # Rename columns based on the profile's mapping
            if "column_mapping" in profile:
                data = data.rename(columns=profile["column_mapping"])

            # Convert to a list of dictionaries for JSON compatibility
            output_data = data.to_dict(orient='records')

            logging.info(f"[CSVIngestor] Successfully ingested {len(output_data)} records from {filepath}.")
            return {
                "status": "success",
                "record_count": len(output_data),
                "data": output_data
            }

        except FileNotFoundError:
            logging.error(f"[CSVIngestor] CSV file not found at: {filepath}")
            return {"status": "error", "message": f"File not found: {filepath}"}
        except Exception as e:
            logging.error(f"[CSVIngestor] An error occurred during CSV ingestion: {e}")
            return {"status": "error", "message": str(e)}