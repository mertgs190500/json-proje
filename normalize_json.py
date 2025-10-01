import json
import os

def normalize_file(source_filename, target_filename):
    """Loads a JSON file and saves it with standard formatting."""
    print(f"Normalizing {source_filename} -> {target_filename}...")
    try:
        with open(source_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(target_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Successfully created {target_filename}.")
        return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error processing {source_filename}: {e}")
        return False

def main():
    print("--- Starting Normalization Step ---")

    # Normalize v15 file
    normalize_file('uretim_cekirdek_v15_revised.json', 'v15_normalized.json')

    # Normalize finalv1 file
    normalize_file('finalv1.json', 'finalv1_normalized.json')

    print("\n--- File Sizes After Normalization ---")
    os.system('ls -lh *.json')

    print("\n--- Normalization Complete ---")

if __name__ == "__main__":
    main()