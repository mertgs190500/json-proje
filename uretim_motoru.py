# Akıllı Üretim Motoru
# Bu script, uretim_cekirdek_v15_revised.json dosyasını bir kural motoru olarak kullanarak
# SEO ve veri işleme görevlerini dinamik olarak yönetir.

import os
import json
import hashlib
import sys

def verify_json_integrity(filepath):
    """
    Verilen JSON dosyasının SHA256 hash'ini hesaplar ve dosya içindeki
    beklenen hash ile karşılaştırarak bütünlüğünü doğrular.
    """
    try:
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
        calculated_hash = hashlib.sha256(file_bytes).hexdigest()

        config_data = json.loads(file_bytes.decode('utf-8'))

        expected_hash = config_data.get("sg", {}).get("expected_sha256")

        if not expected_hash:
            print(f"HATA: '{filepath}' içinde beklenen SHA256 hash'i (/sg/expected_sha256) bulunamadı.")
            return None

        if calculated_hash == expected_hash:
            return config_data
        else:
            print("--- GÜVENLİK UYARISI: BÜTÜNLÜK ---")
            print(f"HATA: '{filepath}' dosyasının bütünlüğü doğrulanamadı.")
            print(f"Hesaplanan SHA256: {calculated_hash}")
            print(f"Beklenen SHA256:   {expected_hash}")
            return None

    except Exception as e:
        print(f"HATA: Bütünlük kontrolü sırasında beklenmedik bir hata oluştu: {e}")
        return None

def load_config(filepath):
    """Yapılandırma dosyasını yükler ve bütünlüğünü doğrular."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        verified_config = verify_json_integrity(filepath)
        if not verified_config:
             sys.exit(1)
        print("-> Yapılandırma başarıyla yüklendi ve doğrulandı.")
        return verified_config

    except FileNotFoundError:
        print(f"HATA: Yapılandırma dosyası bulunamadı: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"HATA: Yapılandırma dosyası geçerli bir JSON formatında değil: {filepath}")
        sys.exit(1)

def manage_state(config, data=None, mode='read'):
    """
    Durum dosyasını (RUN_STATE.json) yönetir. Veri küçülme koruması içerir.
    """
    state_filepath = config.get("fs", {}).get("rt_p", {}).get("run_state_file", "RUN_STATE.json")

    if mode == 'read':
        try:
            with open(state_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None # Dosya yoksa veya bozuksa None döndür

    elif mode == 'write':
        if data is None: return False
        new_state_bytes = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')

        guard_rules = config.get("pl", {}).get("security", {}).get("size_shrink_guard", {})
        if guard_rules and os.path.exists(state_filepath):
            new_size = len(new_state_bytes)
            try:
                old_size = os.path.getsize(state_filepath)
                if old_size > 0:
                    size_diff = old_size - new_size
                    threshold_bytes = guard_rules.get("threshold_bytes", 4096)
                    threshold_ratio = guard_rules.get("threshold_percent", 0.005)
                    shrink_ratio_actual = size_diff / old_size

                    is_over_byte_threshold = size_diff > threshold_bytes
                    is_over_percent_threshold = shrink_ratio_actual > threshold_ratio

                    if is_over_byte_threshold or is_over_percent_threshold:
                        shrink_percent_display = shrink_ratio_actual * 100
                        threshold_percent_display = threshold_ratio * 100

                        print("--- GÜVENLİK UYARISI: VERİ KÜÇÜLMESİ ---")
                        print(f"Durum dosyası boyutu tehlikeli oranda küçüldü.")
                        print(f"  Eski Boyut: {old_size} bytes, Yeni Boyut: {new_size} bytes")
                        print(f"  Fark: -{size_diff} bytes ({shrink_percent_display:.2f}%)")
                        print(f"Eşikler: >{threshold_bytes} bytes VEYA >{threshold_percent_display:.1f}%")

                        if guard_rules.get("on_violation") == "block_and_request_approval":
                            print("İşlem durduruldu. Veri kaybını önlemek için yazma işlemi iptal edildi.")
                            return False
            except Exception as e:
                print(f"UYARI: Küçülme koruması çalışırken bir hata oluştu: {e}")

        try:
            with open(state_filepath, 'w', encoding='utf-8') as f:
                 f.write(new_state_bytes.decode('utf-8'))
            return True
        except Exception as e:
            print(f"HATA: Durum dosyası yazılırken hata oluştu: {e}")
            return False
    return None

def main():
    print("Akıllı Üretim Motoru Başlatılıyor...")
    config_filepath = "uretim_cekirdek_v15_revised.json"

    config = load_config(config_filepath)

    if config:
        # Ana motor mantığı buraya gelecek
        pass

if __name__ == "__main__":
    main()