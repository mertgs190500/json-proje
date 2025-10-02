import json
from collections import OrderedDict

def load_json_file(filename):
    """Loads a JSON file with an ordered dictionary hook."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        print(f"HATA: Dosya bulunamadı: {filename}")
        return None
    except json.JSONDecodeError as e:
        print(f"HATA: JSON formatı bozuk: {filename}. Detay: {e}")
        return None

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"BAŞARILI: Birleştirilmiş dosya kaydedildi: {filename}")

def deep_merge(target, source):
    """
    Recursively merges source into target.
    - If a key exists in both and values are dicts, merge them.
    - If a key exists in both and values are lists, it does not replace the target list.
    - If a key from source does not exist in target, it's added.
    - If a key exists in both but the target's value is an empty list or dict,
      it will be populated with the source's value.
    """
    for key, value in source.items():
        if key in target:
            target_value = target[key]
            if isinstance(target_value, dict) and isinstance(value, dict):
                deep_merge(target_value, value)
            # This is the crucial part: only populate if target is empty
            elif isinstance(target_value, list) and isinstance(value, list) and not target_value:
                target[key] = value
            elif isinstance(target_value, dict) and isinstance(value, dict) and not target_value:
                 target[key] = value
        else:
            # If the key doesn't exist in the target, add it.
            target[key] = value
    return target

def main():
    """Main function to load files, run the deep merge, and save."""
    source_file = 'uretim_cekirdek_v15_revised.json'
    target_file = 'finalv1.json'

    print(f"Kaynak dosya yükleniyor: {source_file}")
    source_data = load_json_file(source_file)

    print(f"Hedef dosya yükleniyor: {target_file}")
    target_data = load_json_file(target_file)

    if source_data is None or target_data is None:
        print("Dosya yükleme hatası nedeniyle birleştirme yapılamadı.")
        return

    print("\n'v15' verisi 'finalv1.json' dosyasına derin birleştiriliyor...")
    # The target is the first argument, the source is the second.
    merged_data = deep_merge(target_data, source_data)

    print("\nBirleştirme tamamlandı. Sonuç dosyası kaydediliyor...")
    save_json_file(merged_data, target_file)

    print(f"\nNİHAİ GÖREV BAŞARIYLA TAMAMLANDI. {target_file} güncellendi.")

if __name__ == "__main__":
    main()