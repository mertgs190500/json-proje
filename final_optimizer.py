import json
import collections
import hashlib
from copy import deepcopy

def get_node_size(node):
    """Bir JSON düğümünün kompakt dize olarak boyutunu bayt cinsinden hesaplar."""
    return len(json.dumps(node, separators=(',', ':')))

def apply_profitable_deduplication(data):
    """
    Yalnızca karlıysa tekrar eden nesneleri referanslarla değiştirir.
    """
    print("Adım 1: Kârlı Nesneleri Referanslama...")

    structures = collections.defaultdict(list)

    def finder(obj, path=""):
        if isinstance(obj, dict) and ("$ref" in obj or path.startswith('/_defs') or path.startswith('/audit')):
            return

        try:
            key = json.dumps(obj, sort_keys=True)
            if isinstance(obj, (dict, list)) and len(obj) > 0:
                 structures[key].append(path)
        except TypeError:
            return

        if isinstance(obj, dict):
            for k, v in obj.items():
                finder(v, f"{path}/{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                finder(item, f"{path}/{i}")

    finder(data)

    duplicates = {k: v for k, v in structures.items() if len(v) > 1}

    if not duplicates:
        print("  - Kârlı tekrar eden nesne bulunamadı.")
        return data

    if '_defs' not in data:
        data['_defs'] = {}

    def_counter = len(data.get('_defs', {}))
    replaced_paths = set()

    for struct_str, paths in duplicates.items():
        original_obj = json.loads(struct_str)
        num_occurrences = len(paths)

        gain = get_node_size(original_obj) * num_occurrences

        def_id = f"def_auto_{def_counter}"
        ref_obj = {"$ref": f"#/_defs/{def_id}"}
        # _defs'e eklenecek tanımın maliyeti. {} hariç, anahtar + ':' + değer.
        cost_def = len(f'"{def_id}":{json.dumps(original_obj, separators=(",", ":"))}')

        cost_refs = get_node_size(ref_obj) * num_occurrences
        cost = cost_def + cost_refs

        # Sadece karlı ise optimizasyonu uygula
        if gain > cost:
            def_counter += 1
            print(f"  - Uygulanıyor: {num_occurrences} adet nesne '{def_id}' olarak referanslandı. Kazanç: {(gain - cost) / 1024:.2f} KB")

            data['_defs'][def_id] = original_obj

            for path in paths:
                if any(path.startswith(p + '/') for p in replaced_paths):
                    continue

                parts = path.strip('/').split('/')
                curr = data
                try:
                    for part in parts[:-1]:
                        curr = curr[int(part) if part.isdigit() else part]

                    key = parts[-1]
                    curr[int(key) if key.isdigit() else key] = deepcopy(ref_obj)
                    replaced_paths.add(path)
                except (KeyError, IndexError, TypeError):
                    continue

    if not any(k.startswith("def_auto_") for k in data.get('_defs', {})):
        if data.get('_defs') == {}:
            del data['_defs']

    return data

def apply_datatype_optimization(data):
    """
    Boolean değerleri 1/0'a ve karlı enumları sayısala dönüştürür.
    """
    print("\nAdım 2: Veri Tipi Optimizasyonu...")

    strings = collections.Counter()
    bool_count = {'true': 0, 'false': 0}
    def value_finder(obj):
        if isinstance(obj, dict):
            for v in obj.values(): value_finder(v)
        elif isinstance(obj, list):
            for item in obj: value_finder(item)
        elif isinstance(obj, str):
            if 3 < len(obj) < 50 and obj.replace('_', '').isalnum():
                strings[obj] += 1
        elif isinstance(obj, bool):
            bool_count['true' if obj else 'false'] += 1

    value_finder(data)

    profitable_enums = {}
    enum_counter = 0
    for s, count in strings.items():
        if count > 1:
            original_size = (len(s) + 2) * count
            optimized_size = len(str(enum_counter)) * count
            if original_size > optimized_size:
                profitable_enums[s] = enum_counter
                enum_counter += 1

    if profitable_enums:
        print(f"  - {len(profitable_enums)} adet kârlı metin türü sayısallaştırılıyor.")
    if bool_count['true'] > 0 or bool_count['false'] > 0:
        print(f"  - {bool_count['true'] + bool_count['false']} adet boolean değeri 1/0'a çevriliyor.")

    enum_map = {}

    def optimizer(obj):
        nonlocal enum_map
        if isinstance(obj, dict):
            return {k: optimizer(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [optimizer(item) for item in obj]
        elif isinstance(obj, bool):
            return 1 if obj else 0
        elif isinstance(obj, str) and obj in profitable_enums:
            if obj not in enum_map:
                enum_map[obj] = profitable_enums[obj]
            return profitable_enums[obj]
        else:
            return obj

    optimized_data = optimizer(data)

    if enum_map:
        optimized_data['enum_map'] = {v: k for k, v in enum_map.items()}

    return optimized_data


def optimize_json(input_path, output_path):
    """JSON dosyasını hedeflenmiş ve karlı adımlara göre optimize eder."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data = apply_profitable_deduplication(data)
    data = apply_datatype_optimization(data)

    print("\nAdım 3: Denetim bilgileri ve hash güncelleniyor...")
    final_audit = data.pop('audit', {})

    new_sha256 = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

    if 'integrity_hashes' not in final_audit:
        final_audit['integrity_hashes'] = {}
    final_audit['version'] = "11.0.0-machine-optimized"
    final_audit['description'] = "Machine-readable efficiency. Applied profitable-only optimizations: deduplication and data-type optimization."
    final_audit['integrity_hashes']['sha256'] = new_sha256

    data['audit'] = final_audit

    print(f"\nOptimizasyon tamamlandı. Dosya '{output_path}' olarak kaydediliyor.")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

if __name__ == "__main__":
    INPUT_FILE = "uretim_cekirdek_v2.json"
    OUTPUT_FILE = "uretim_cekirdek_v11_machine_optimized.json"
    optimize_json(INPUT_FILE, OUTPUT_FILE)
    print("İşlem başarıyla tamamlandı.")