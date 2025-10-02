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
    print(f"BAŞARILI: Düzeltilmiş dosya kaydedildi: {filename}")

def main():
    """Main function to load, correct, and save the JSON file."""
    target_file = 'finalv1.json'

    print(f"Düzeltilecek dosya yükleniyor: {target_file}")
    data = load_json_file(target_file)

    if data is None:
        print("Dosya yükleme hatası nedeniyle düzeltme yapılamadı.")
        return

    # --- Cerrahi Düzeltmeler ---
    print("Veri tipi düzeltmeleri uygulanıyor...")

    # 1. Listeye Dönüştürülecek Alanlar
    paths_to_list = [
        ("run", "s", "00", "o"),
        ("run", "s", "11", "i"),
        ("run", "s", "14", "i"),
        ("run", "s", "19", "i"),
        ("run", "s", "19", "o"),
        ("run", "s", "5a", "o"),
        ("run", "s", "7", "o"),
        ("run", "s", "8a", "i"),
        ("run", "s", "8a", "o"),
        ("run", "s", "seo_package", "i"),
        ("run", "s", "8C", "i")
    ]
    for path in paths_to_list:
        try:
            data[path[0]][path[1]][path[2]][path[3]] = []
            print(f"  - '{'.'.join(path)}' listeye dönüştürüldü.")
        except KeyError:
            print(f"  - UYARI: '{'.'.join(path)}' yolu bulunamadı, atlanıyor.")


    # 2. Sözlüğe Dönüştürülecek Alanlar
    paths_to_dict = [
        ("run", "s", "1a", "rs"),
        ("run", "s", "5a", "rs"),
        ("run", "s", "7", "rs")
    ]
    for path in paths_to_dict:
        try:
            data[path[0]][path[1]][path[2]][path[3]] = OrderedDict()
            print(f"  - '{'.'.join(path)}' sözlüğe dönüştürüldü.")
        except KeyError:
            print(f"  - UYARI: '{'.'.join(path)}' yolu bulunamadı, atlanıyor.")

    # 3. Dosyayı Kaydet
    save_json_file(data, target_file)
    print("\nDüzeltme işlemi tamamlandı.")


if __name__ == "__main__":
    main()