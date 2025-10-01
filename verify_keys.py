import json
from collections.abc import Mapping, Sequence

def get_all_keys(d, parent_key=''):
    """
    Recursively get all keys from a nested dictionary.
    """
    keys = set()
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        keys.add(new_key)
        if isinstance(v, Mapping):
            keys.update(get_all_keys(v, new_key))
        # We don't need to traverse into lists for key extraction
    return keys

def find_missing_keys(source_dict, target_dict):
    """
    Find keys that are in source_dict but not in target_dict.
    This function will be more complex to handle nested structures correctly.
    """
    missing_keys = []

    def check_keys(s_dict, t_dict, path=""):
        for key, s_value in s_dict.items():
            current_path = f"{path}.{key}" if path else key
            if key not in t_dict:
                missing_keys.append(current_path)
            elif isinstance(s_value, dict) and isinstance(t_dict.get(key), dict):
                check_keys(s_value, t_dict[key], current_path)

    check_keys(source_dict, target_dict)
    return missing_keys


def main():
    try:
        with open('uretim_cekirdek_v15_revised.json', 'r', encoding='utf-8') as f:
            v15_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading uretim_cekirdek_v15_revised.json: {e}")
        return

    try:
        with open('finalv1.json', 'r', encoding='utf-8') as f:
            final_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading finalv1.json: {e}")
        return

    print("Verifying keys...")
    missing_keys_list = find_missing_keys(v15_data, final_data)

    if not missing_keys_list:
        print("Veri Kaybı Tespiti Sonucu: Hayır, v15'teki anahtarlardan finalv1'de eksik olan YOKTUR.")
    else:
        print("Veri Kaybı Tespiti Sonucu: Evet, v15'teki şu anahtarlar finalv1'de eksik:")
        for key in missing_keys_list:
            print(f"- {key}")

if __name__ == "__main__":
    main()