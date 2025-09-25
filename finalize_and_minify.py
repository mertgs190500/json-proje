import json
import hashlib
from copy import deepcopy

def rename_gpt_do_recursive(data):
    """
    Recursively finds 'gpt_do' keys under a given data structure and renames them to 'gemini_do'.
    """
    if isinstance(data, dict):
        if 'gpt_do' in data:
            data['gemini_do'] = data.pop('gpt_do')
        for key, value in data.items():
            rename_gpt_do_recursive(value)
    elif isinstance(data, list):
        for item in data:
            rename_gpt_do_recursive(item)

def finalize_and_minify(input_path, output_path):
    """
    Performs terminology update, minification, and re-sealing of the JSON file.
    """
    print(f"Reading data from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Adım 2.b: Terminoloji Düzeltmesi
    print("Renaming 'gpt_do' to 'gemini_do' under /run/s/...")
    if 'run' in data and 's' in data['run']:
        rename_gpt_do_recursive(data['run']['s'])
        print("Rename operation completed.")
    else:
        print("Warning: Path /run/s/ not found. Skipping rename operation.")

    # Adım 2.c & 2.d: Minification, Hash Hesaplama ve Güvenlik Mührünü Güncelleme
    print("Calculating new hash and updating security locks...")

    # Create a deep copy for hashing to avoid the hash being affected by its own value.
    data_for_hashing = deepcopy(data)

    # Temporarily remove old lock values from the copy to calculate the new hash.
    # This ensures the hash is of the content, not the content + old hash.
    if 'fs' in data_for_hashing and 'lock' in data_for_hashing['fs']:
        data_for_hashing['fs']['lock'] = None
    if 'sg' in data_for_hashing and 'expected_sha256' in data_for_hashing['sg']:
        data_for_hashing['sg']['expected_sha256'] = None

    # Minify the JSON string by removing all non-essential whitespace.
    minified_string = json.dumps(data_for_hashing, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    # Calculate the new hash from the minified content.
    new_hash = hashlib.sha256(minified_string).hexdigest()
    print(f"New SHA256 hash: {new_hash}")

    # Update the locks in the original data structure with the new hash.
    if 'fs' in data and 'lock' in data['fs']:
        data['fs']['lock'] = new_hash
        print(f"Updated /fs/lock with new hash.")
    else:
        print("Warning: /fs/lock path not found for updating.")

    if 'sg' in data and 'expected_sha256' in data['sg']:
        data['sg']['expected_sha256'] = new_hash
        print(f"Updated /sg/expected_sha256 with new hash.")
    else:
        print("Warning: /sg/expected_sha256 path not found for updating.")

    # Save the final, minified file.
    print(f"Saving minified and updated file to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print("Process completed successfully.")

if __name__ == "__main__":
    INPUT_FILE = "uretim_cekirdek_v2.json"
    OUTPUT_FILE = "uretim_cekirdek_v12_final_minified.json"
    finalize_and_minify(INPUT_FILE, OUTPUT_FILE)