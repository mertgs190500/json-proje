import json
import logging
import pandas as pd
from csv_ingestor import CsvIngestor
from data_loader import DataLoader

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_profiles():
    """Loads CSV profiles from the JSON file."""
    try:
        with open('csv_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f).get("profiles", {})
    except FileNotFoundError:
        logging.error("FATAL: csv_profiles.json not found.")
        return None

def run_test(ingestor, data_loader, file_path, profile_name, profiles, validation_fn):
    """
    Runs a single CSV parsing test case.

    Args:
        ingestor (CsvIngestor): An instance of the CsvIngestor.
        data_loader (DataLoader): An instance of the DataLoader.
        file_path (str): Path to the test CSV file.
        profile_name (str): The name of the profile to use for ingestion.
        profiles (dict): The dictionary of all loaded profiles.
        validation_fn (function): A function to validate the parsed data.

    Returns:
        bool: True if the test passed, False otherwise.
    """
    logging.info(f"--- Running Test for: {file_path} with Profile: {profile_name} ---")

    # 1. Load raw content
    raw_content_result = data_loader.execute({"file_path": file_path}, {})
    if raw_content_result is None or 'raw_content' not in raw_content_result:
        logging.error(f"Failed to load raw content for {file_path}.")
        return False

    # 2. Prepare inputs for ingestor
    ingestor_inputs = {
        "raw_content": raw_content_result['raw_content'],
        "resolved_profile": profiles.get(profile_name)
    }

    # 3. Execute the ingestor
    result = ingestor.execute(ingestor_inputs, {})

    # 4. Validate the result
    if result['status'] != 'success':
        logging.error(f"Ingestion failed for {file_path}. Message: {result['message']}")
        return False

    parsed_data = result['data']
    if not parsed_data:
        logging.error(f"Ingestion succeeded but produced no data for {file_path}.")
        return False

    try:
        validation_fn(parsed_data)
        logging.info(f"SUCCESS: Validation passed for {file_path}.")
        return True
    except AssertionError as e:
        logging.error(f"FAIL: Validation failed for {file_path}. Error: {e}")
        logging.error(f"Parsed Data Snapshot: {json.dumps(parsed_data[:2], indent=2)}") # Log first 2 records
        return False

# --- Validation Functions ---

def validate_similar(data):
    """Validation logic for test_similar.csv"""
    # Expected headers: Keyword, Search volume, Competition
    assert len(data[0].keys()) == 3, f"Expected 3 columns, but got {len(data[0].keys())}"
    # Check if the empty keyword was processed
    assert data[4]['Keyword'] is None or pd.isna(data[4]['Keyword']), "Empty keyword field was not handled as NA"
    # Check if NULL was processed in the correct column ('Search volume')
    assert pd.isna(data[5]['Search volume']), "NULL value was not handled as NA"
    logging.info("`similar_keywords` validation checks passed.")

def validate_top_listings(data):
    """Validation logic for test_top_listings.csv"""
    # Expected headers: Title, Price, Tags (ID is index)
    assert len(data[0].keys()) == 3, f"Expected 3 columns, but got {len(data[0].keys())}"
    # Check title with comma
    assert data[0]['Title'] == "Ring, 14K Gold, Handmade", "Title with commas was not parsed correctly."
    # Check tags with comma
    assert data[0]['Tags'] == "gold ring,wedding band,engagement", "Tags with commas were not parsed correctly."
    # Check custom name with comma
    assert data[2]['Title'] == "Custom Name Necklace, Gold Plated", "Second title with commas not parsed correctly."
    logging.info("`top_listings` validation checks passed.")

def validate_listings(data):
    """Validation logic for test_listings.csv"""
    # Expected headers: Title, URL, Sales (ID is index)
    assert len(data[0].keys()) == 3, f"Expected 3 columns, but got {len(data[0].keys())}"
    # Check title with comma
    assert data[3]['Title'] == "Gemstone Ring, Emerald Cut", "Title with commas was not parsed correctly."
    logging.info("`listings` validation checks passed.")

def main():
    """Main function to orchestrate the tests."""
    profiles = load_profiles()
    if not profiles:
        return

    ingestor = CsvIngestor()
    data_loader = DataLoader()

    test_cases = [
        ("test_similar.csv", "similar_keywords_v2", validate_similar),
        ("test_top_listings.csv", "top_listings_title_first_v1", validate_top_listings),
        ("test_listings.csv", "listings_title_first_v1", validate_listings)
    ]

    results = []
    for file_path, profile_name, validation_fn in test_cases:
        is_success = run_test(ingestor, data_loader, file_path, profile_name, profiles, validation_fn)
        results.append((file_path, "PASS" if is_success else "FAIL"))

    print("\n--- CSV PARSING VERIFICATION REPORT ---")
    for file_path, status in results:
        print(f"{file_path:<25} | Status: {status}")
    print("---------------------------------------")

    if all(status == "PASS" for _, status in results):
        print("\nAll CSV parsing tests passed successfully!")
    else:
        print("\nSome CSV parsing tests failed. Please review the logs above.")

if __name__ == "__main__":
    main()