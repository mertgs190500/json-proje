import json
import collections
import hashlib
from copy import deepcopy

def apply_deduplication(data):
    """
    Tekrar eden tüm nesneleri analiz eder ve referanslarla değiştirir.
    """
    print("Adım 1: Tekrar Eden Nesneler Referanslanıyor...")

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
        print("  - Tekrar eden nesne bulunamadı.")
        return data

    if '_defs' not in data:
        data['_defs'] = {}

    # Mevcut def'leri sayarak çakışmayı önle
    def_counter = len(data.get('_defs', {}))
    # Benzersiz ID'ler için mevcut def ID'lerindeki sayıları bul
    existing_def_ids = [int(k.split('_')[-1]) for k in data.get('_defs', {}).keys() if k.startswith('def_') and k.split('_')[-1].isdigit()]
    if existing_def_ids:
        def_counter = max(existing_def_ids) + 1

    replaced_paths = set()

    for struct_str, paths in duplicates.items():
        original_obj = json.loads(struct_str)
        num_occurrences = len(paths)

        def_id = f"def_auto_{def_counter}"
        def_counter += 1

        print(f"  - {num_occurrences} adet nesne '{def_id}' olarak referanslanıyor.")
        ref_obj = {"$ref": f"#/_defs/{def_id}"}

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
    return data

def apply_key_shortening(data):
    """
    Tüm anahtarları sistematik olarak kısaltır ve bir key_map oluşturur.
    """
    print("\nAdım 2: Anahtarlar Kısaltılıyor...")
    key_map = {}
    key_counter = 0

    # Önemli not: _defs, audit gibi özel anahtarları kısaltma dışında tutmuyoruz.
    # Talimat, *tüm* anahtarların kısaltılmasını istiyor.

    def shorten_keys_recursive(obj):
        nonlocal key_map, key_counter
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                if k not in key_map:
                    new_key = f"k{key_counter}"
                    key_map[k] = new_key
                    key_counter += 1
                else:
                    new_key = key_map[k]
                new_obj[new_key] = shorten_keys_recursive(v)
            return new_obj
        elif isinstance(obj, list):
            return [shorten_keys_recursive(item) for item in obj]
        else:
            return obj

    shortened_data = shorten_keys_recursive(data)

    # key_map'i tersine çevirerek (kısa -> uzun) dosyaya ekle
    # Bu, haritanın kendisinin de anahtarlarının kısaltılmasını önler.
    shortened_data['key_map'] = {v: k for k, v in key_map.items()}

    print(f"  - {len(key_map)} adet benzersiz anahtar kısaltıldı.")
    return shortened_data

def apply_datatype_optimization(data):
    """
    Boolean değerleri 1/0'a ve tüm uygun stringleri sayısala dönüştürür.
    """
    print("\nAdım 3: Veri Tipleri Optimize Ediliyor...")

    strings = collections.Counter()
    bool_count = {'true': 0, 'false': 0}
    def value_finder(obj):
        # key_map ve enum_map'in değerlerini analiz dışında tut
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ['key_map', 'enum_map']: continue
                value_finder(v)
        elif isinstance(obj, list):
            for item in obj: value_finder(item)
        elif isinstance(obj, str):
            # Enum adayı olabilecek stringleri topla
            if 3 < len(obj) < 50 and obj.replace('_', '').isalnum():
                strings[obj] += 1
        elif isinstance(obj, bool):
            bool_count['true' if obj else 'false'] += 1

    value_finder(data)

    # Enum'a dönüştürülecek string'leri belirle
    enums_to_convert = {s: i for i, (s, count) in enumerate(strings.items()) if count > 1}

    print(f"  - {len(enums_to_convert)} adet metin türü sayısallaştırılıyor.")
    print(f"  - {bool_count['true'] + bool_count['false']} adet boolean değeri 1/0'a çevriliyor.")

    enum_map = {}

    def optimizer(obj, current_path=""):
        nonlocal enum_map
        if isinstance(obj, dict):
            # Haritalama objelerinin içine dokunma
            if current_path in ['/key_map', '/enum_map']:
                return obj
            return {k: optimizer(v, f"{current_path}/{k}") for k, v in obj.items()}
        elif isinstance(obj, list):
            return [optimizer(item, current_path) for item in obj]
        elif isinstance(obj, bool):
            return 1 if obj else 0
        elif isinstance(obj, str) and obj in enums_to_convert:
            enum_map[obj] = enums_to_convert[obj]
            return enums_to_convert[obj]
        else:
            return obj

    optimized_data = optimizer(data)

    if enum_map:
        optimized_data['enum_map'] = {v: k for k, v in enum_map.items()}

    return optimized_data


def optimize_json(input_path, output_path):
    """JSON dosyasını verilen tüm adımlara göre optimize eder."""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Adım 1: Referanslama
    data = apply_deduplication(data)

    # Adım 2: Anahtar Kısaltma
    data = apply_key_shortening(data)

    # Adım 3: Veri Tipi Optimizasyonu
    data = apply_datatype_optimization(data)

    # Adım 4: Denetim ve Hash Güncellemesi
    print("\nAdım 4: Denetim Bilgileri ve Hash Güncelleniyor...")

    # Adım 4: Denetim ve Hash Güncellemesi
    print("\nAdım 4: Denetim Bilgileri ve Hash Güncelleniyor...")

    # Önce anahtar haritasını alalım, çünkü tüm diğer anahtarları bulmak için ona ihtiyacımız var.
    key_map_data = data.get('key_map')
    if not key_map_data:
        raise ValueError("key_map not found in the data.")

    original_key_map = {v: k for k, v in key_map_data.items()}
    s_audit = original_key_map.get('audit')
    if not s_audit:
        raise ValueError("'audit' key not found in key_map.")

    # Hash hesaplaması için verinin bir kopyasını oluştur ve ilgili bölümleri çıkar
    data_for_hash = deepcopy(data)

    # Haritaları en üst seviyeden kaldır
    del data_for_hash['key_map']
    data_for_hash.pop('enum_map', None)

    # Audit bloğunu, nerede olursa olsun, kopyadan kaldır
    def find_and_remove(obj, key_to_remove):
        if isinstance(obj, dict):
            if key_to_remove in obj:
                del obj[key_to_remove]
                return True
            for value in obj.values():
                if find_and_remove(value, key_to_remove):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if find_and_remove(item, key_to_remove):
                    return True
        return False

    if not find_and_remove(data_for_hash, s_audit):
        print("  - Uyarı: Hash hesaplaması için audit bloğu bulunamadı/kaldırılamadı.")

    # Geriye kalan verinin hash'ini hesapla
    new_sha256 = hashlib.sha256(json.dumps(data_for_hash, sort_keys=True).encode('utf-8')).hexdigest()

    # Şimdi orijinal 'data' objesindeki audit bloğunu bul ve güncelle
    s_version = original_key_map.get('version', 'version')
    s_desc = original_key_map.get('description', 'description')
    s_hashes = original_key_map.get('integrity_hashes', 'integrity_hashes')
    s_sha256 = original_key_map.get('sha256', 'sha256')

    def find_and_update(obj, key_to_find):
        if isinstance(obj, dict):
            if key_to_find in obj:
                audit_block = obj[key_to_find]
                audit_block[s_version] = "11.0.0-machine-optimized"
                audit_block[s_desc] = "Machine-readable efficiency. Applied ALL optimizations: deduplication, key shortening, and data-type optimization as per instructions."
                if s_hashes not in audit_block:
                    audit_block[s_hashes] = {}
                audit_block[s_hashes][s_sha256] = new_sha256
                return True
            for value in obj.values():
                if find_and_update(value, key_to_find):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if find_and_update(item, key_to_find):
                    return True
        return False

    if not find_and_update(data, s_audit):
        print("  - Uyarı: Orijinal veride audit bloğu bulunamadı/güncellenemedi.")

    # Son dosyayı kaydet
    print(f"\nOptimizasyon tamamlandı. Dosya '{output_path}' olarak kaydediliyor.")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

if __name__ == "__main__":
    INPUT_FILE = "uretim_cekirdek_v2.json"
    OUTPUT_FILE = "uretim_cekirdek_v11_machine_optimized.json"
    optimize_json(INPUT_FILE, OUTPUT_FILE)
    print("İşlem başarıyla tamamlandı.")