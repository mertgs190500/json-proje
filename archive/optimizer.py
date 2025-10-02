import json
import hashlib
from collections import Counter

def get_hash(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()

def optimize_json(filepath, output_filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Referencing and Normalization (_defs Genişletmesi)
    defs_map = {}
    defs_list = []

    def find_and_replace_common_objects(obj):
        if isinstance(obj, dict):
            for key, value in list(obj.items()):
                if isinstance(value, (dict, list)):
                    find_and_replace_common_objects(value)
                    if key != '_defs' and len(json.dumps(value)) >= 50:
                        obj_hash = get_hash(value)
                        if obj_hash not in defs_map:
                            defs_map[obj_hash] = len(defs_list)
                            defs_list.append(value)
                        obj[key] = {"$ref": f"#/_defs/{defs_map[obj_hash]}"}
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    find_and_replace_common_objects(item)
                    if len(json.dumps(item)) >= 50:
                        item_hash = get_hash(item)
                        if item_hash not in defs_map:
                            defs_map[item_hash] = len(defs_list)
                            defs_list.append(item)
                        obj[i] = {"$ref": f"#/_defs/{defs_map[item_hash]}"}

    find_and_replace_common_objects(data)
    data['_defs'] = defs_list

    # 2. Anahtar (Key) Kısaltma ve Haritalama
    keys = Counter()
    def count_keys(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                keys[key] += 1
                count_keys(value)
        elif isinstance(obj, list):
            for item in obj:
                count_keys(item)

    count_keys(data)

    key_map = {}
    short_key_counter = 0
    for key, count in keys.most_common():
        if count > 5 and len(key) > 3: # Only shorten keys that appear more than 5 times
            short_key = f"k{short_key_counter}"
            key_map[short_key] = key
            short_key_counter += 1

    def replace_keys(obj):
        if isinstance(obj, dict):
            new_obj = {}
            for key, value in obj.items():
                new_key = key
                for short_key, long_key in key_map.items():
                    if long_key == key:
                        new_key = short_key
                        break
                new_obj[new_key] = replace_keys(value)
            return new_obj
        elif isinstance(obj, list):
            return [replace_keys(item) for item in obj]
        else:
            return obj

    data = replace_keys(data)
    data['key_map'] = key_map

    # 3. Veri Tipi Optimizasyonu
    enum_map = {
        0: "approved",
        1: "halt_and_report",
        2: "warn_and_continue"
    }

    def optimize_data_types(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = optimize_data_types(value)
        elif isinstance(obj, list):
            return [optimize_data_types(item) for item in obj]
        elif isinstance(obj, bool):
            return 1 if obj else 0
        elif isinstance(obj, str):
            for k, v in enum_map.items():
                if obj == v:
                    return k
        return obj

    data = optimize_data_types(data)
    data['enum_map'] = enum_map

    # 4. Update metadata and hash
    if '_meta' not in data:
        data['_meta'] = {}
    data['_meta']['optimization_notes'] = "Structural optimization and size reduction applied."

    if 'new_sha256' in data.get('_meta', {}):
        del data['_meta']['new_sha256']

    new_sha256 = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    data['_meta']['new_sha256'] = new_sha256

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

if __name__ == "__main__":
    optimize_json("uretim_cekirdek_v2.json", "uretim_cekirdek_v9_optimized.json")