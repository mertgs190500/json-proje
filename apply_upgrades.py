# apply_upgrades.py (v6 - Kodu Veriden Ayıran Final Versiyon)

import json
import requests
from collections import OrderedDict

# --- KONFİGÜRASYON ---
SOURCE_URL = 'https://raw.githubusercontent.com/mertgs190500/json-proje/refs/heads/main/uretim_cekirdek_v15_revised.json'
LOCAL_SOURCE_FILE = 'uretim_cekirdek_v15_revised.json'
CHANGES_V16_FILE = 'changes_v16.json'
CHANGES_V17_FILE = 'changes_v17.json'
TARGET_FILE = 'finalv1.json'

# --- YARDIMCI FONKSİYONLAR ---

def download_file(url, local_filename):
    print(f"Kaynak dosya indiriliyor: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(local_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"Kaynak dosya başarıyla indirildi ve '{local_filename}' olarak kaydedildi.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"HATA: Kaynak dosya indirilemedi. Detay: {e}")
        return False

def load_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except FileNotFoundError:
        print(f"HATA: Gerekli dosya bulunamadı: {filename}")
        return None
    except json.JSONDecodeError as e:
        print(f"HATA: JSON formatı bozuk: {filename}. Detay: {e}")
        return None

def save_json_file(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"BAŞARILI: Sonuç dosyası kaydedildi: {filename}")

def deep_update(target, source):
    for key, value in source.items():
        target_value = target.get(key)
        if isinstance(target_value, dict) and isinstance(value, dict):
            deep_update(target_value, value)
        elif isinstance(target_value, list) and isinstance(value, list):
            for item in value:
                if item not in target_value:
                    target_value.append(item)
        elif isinstance(target, dict):
            target[key] = value
    return target

# --- ANA YÜRÜTME ---

def main():
    print("--- Nihai Yükseltme Başlatılıyor (Kodu Veriden Ayırma Stratejisi) ---")

    # Adım 1: Kaynak dosyaları indir ve yükle
    if not download_file(SOURCE_URL, LOCAL_SOURCE_FILE): return

    source_data = load_json_file(LOCAL_SOURCE_FILE)
    changes_v16 = load_json_file(CHANGES_V16_FILE)
    changes_v17 = load_json_file(CHANGES_V17_FILE)

    if not all([source_data, changes_v16, changes_v17]):
        print("HATA: Gerekli dosyaların hepsi yüklenemedi. İşlem durduruldu.")
        return

    # Adım 2: v16 Değişikliklerini uygula
    print("\n--- v16 Değişiklikleri Uygulanıyor ---")
    data_after_v16 = deep_update(source_data, changes_v16)

    # Adım 3: v17 Değişikliklerini uygula
    print("\n--- v17 Değişiklikleri Uygulanıyor ---")
    final_data = deep_update(data_after_v16, changes_v17)

    # Adım 4: Sonucu kaydet
    print("\n--- Yükseltme Tamamlandı. Sonuç dosyası kaydediliyor. ---")
    save_json_file(final_data, TARGET_FILE)
    print(f"\nGÖREV BAŞARIYLA TAMAMLANDI. {TARGET_FILE} oluşturuldu.")

if __name__ == "__main__":
    main()