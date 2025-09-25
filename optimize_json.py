import json
import hashlib
from collections import defaultdict
import re

def find_duplicates(data):
    duplicates = defaultdict(list)

    def _find_duplicates_recursive(obj, path):
        if isinstance(obj, dict):
            try:
                key = tuple(sorted(obj.items()))
                duplicates[key].append(path)
            except (TypeError, ValueError):
                pass

            for k, v in obj.items():
                _find_duplicates_recursive(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _find_duplicates_recursive(item, f"{path}/{i}")

    _find_duplicates_recursive(data, "#")

    return {k: v for k, v in duplicates.items() if len(v) > 1}

def optimize_json(input_filepath, output_filepath):
    with open(input_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Referencing and Normalization
    if '_defs' not in data:
        data['_defs'] = {}

    duplicates = find_duplicates(data)

    for i, (duplicate_obj, paths) in enumerate(duplicates.items()):
        def_id = f"def_{i}"
        data['_defs'][def_id] = dict(duplicate_obj)

        for path in paths:
            parts = path.split('/')[1:]
            current = data
            for part in parts[:-1]:
                current = current[int(part)] if part.isdigit() and isinstance(current, list) else current[part]
            current[int(parts[-1]) if parts[-1].isdigit() and isinstance(current, list) else parts[-1]] = {"$ref": f"#/_defs/{def_id}"}

    # 2. Key Shortening and Mapping
    key_map = {}

    def shorten_keys(obj):
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                short_key = ''.join(re.findall(r'(\b\w)', k)) if len(k) > 10 else k
                if short_key in key_map and key_map[short_key] != k:
                    # Collision detected, generate a new key
                    i = 1
                    while f"{short_key}{i}" in key_map:
                        i += 1
                    short_key = f"{short_key}{i}"

                key_map[short_key] = k
                new_dict[short_key] = shorten_keys(v)
            return new_dict
        elif isinstance(obj, list):
            return [shorten_keys(item) for item in obj]
        else:
            return obj

    new_data = shorten_keys(data)

    # 3. Data Type Optimization
    enum_map = {}

    def optimize_types(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, bool):
                    obj[k] = 1 if v else 0
                elif isinstance(v, str) and v in ["halt_and_report", "approved", "warn_and_continue"]:
                    if v not in enum_map:
                        enum_map[v] = len(enum_map)
                    obj[k] = enum_map[v]
                else:
                    optimize_types(v)
        elif isinstance(obj, list):
            for item in obj:
                optimize_types(item)

    optimize_types(new_data)

    new_data['key_map'] = {v: k for k, v in key_map.items()}
    new_data['enum_map'] = {v: k for k, v in enum_map.items()}

    if '_meta' not in new_data:
        new_data['_meta'] = {}
    new_data['_meta']['optimization_notes'] = "Structural optimization and size reduction applied."

    sha256_hash = hashlib.sha256()
    sha256_hash.update(json.dumps(new_data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    new_data['_meta']['new_sha256'] = sha256_hash.hexdigest()

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"Optimized JSON saved to {output_filepath}")

if __name__ == '__main__':
    optimize_json('uretim_cekirdek_v2.json', 'uretim_cekirdek_v9_optimized.json')