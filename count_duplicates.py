import json
from collections import Counter

def find_list_duplicates(obj):
    """
    Recursively finds all lists in a JSON object and counts duplicate items within them.
    """
    total_duplicates = 0

    if isinstance(obj, dict):
        for key, value in obj.items():
            total_duplicates += find_list_duplicates(value)
    elif isinstance(obj, list):
        # Count occurrences of each item in the list
        # Only count items that are hashable (strings, numbers, tuples)
        try:
            counts = Counter(item for item in obj if isinstance(item, (str, int, float, bool, tuple)))
            for item, count in counts.items():
                if count > 1:
                    total_duplicates += (count - 1)
        except TypeError:
            # This can happen if a list contains unhashable types like dicts or other lists
            # For this specific analysis, we are interested in primitive duplicates.
            pass

        # Also, recurse into any lists or dicts inside this list
        for item in obj:
            total_duplicates += find_list_duplicates(item)

    return total_duplicates

def main():
    print("--- Starting Duplicate Analysis Step ---")

    try:
        with open('uretim_cekirdek_v15_revised.json', 'r', encoding='utf-8') as f:
            v15_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading uretim_cekirdek_v15_revised.json: {e}")
        return

    duplicate_count = find_list_duplicates(v15_data)

    print("\n--- Duplicate Analysis Results ---")
    print(f"Optimizasyon Tespiti: Orijinal v15 dosyasında toplam {duplicate_count} adet tekrar eden (duplicate) liste elemanı tespit edildi.")
    print("--- Analysis Complete ---")

if __name__ == "__main__":
    main()