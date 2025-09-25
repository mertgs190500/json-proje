import json
import hashlib

def update_meta(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if '_meta' not in data:
        data['_meta'] = {}

    data['_meta']['optimization_notes'] = "Structural optimization and size reduction applied."

    # Remove old hash before calculating new one
    if 'new_sha256' in data.get('_meta', {}):
        del data['_meta']['new_sha256']

    new_sha256 = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    data['_meta']['new_sha256'] = new_sha256

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

if __name__ == "__main__":
    update_meta("uretim_cekirdek_v9_optimized.json")