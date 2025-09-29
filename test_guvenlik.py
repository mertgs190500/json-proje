import os
import json
import sys

# Ana motorumuzdan (artık uretim_scripti.py) gerekli fonksiyonları import edelim
from uretim_scripti import durum_yonetimi

def load_and_normalize_config(filepath):
    """
    Yapılandırma dosyasını ham byte olarak okur, satır sonlarını (CRLF -> LF)
    ve UTF-8 BOM'u normalize eder. Bu, dosyanın farklı sistemlerde
    kaydedilmesinden kaynaklanabilecek hash/boyut tutarsızlıklarını önler.
    Ardından JSON olarak ayrıştırır.
    """
    try:
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()

        # UTF-8 BOM kontrolü ve temizliği
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            raw_bytes = raw_bytes[3:]

        # Satır sonlarını LF (\n) formatına normalize et
        normalized_bytes = raw_bytes.replace(b'\r\n', b'\n')

        # Normalize edilmiş byte'ları UTF-8 olarak decode et
        normalized_content = normalized_bytes.decode('utf-8')

        return json.loads(normalized_content)

    except Exception as e:
        print(f"HATA: Normalize edilmiş yapılandırma yüklenemedi: {e}")
        return None

def main():
    """
    Veri küçülme korumasını (artık `durum_yonetimi` içinde) test eder.
    """
    print("--- Güvenlik Özellikleri Test Scripti (Entegre Motor) ---")

    config_filepath = "uretim_cekirdek_v15_revised.json"
    state_filepath = "RUN_STATE.json"

    # 1. Bütünlük kontrolü hatalarını önlemek için normalize edilmiş config'i yükle
    config = load_and_normalize_config(config_filepath)
    if not config:
        sys.exit(1)

    # 2. Bellekte büyük bir başlangıç durumu oluştur
    large_content = "x" * 10 * 1024 # 10KB'lık veri
    initial_adim_id = "initial_setup"
    initial_uretim_verileri = {
        "data": {
            "large_data_block": large_content
        }
    }

    # 3. Bu büyük durumu durum_yonetimi ile dosyaya yaz (Bu, 'old_size' olacak)
    print("-> Test için büyük boyutlu 'RUN_STATE.json' dosyası oluşturuluyor...")
    # Önce varsa eski test dosyasını temizle
    if os.path.exists(state_filepath):
        os.remove(state_filepath)

    initial_write_ok = durum_yonetimi(config, adim_id=initial_adim_id, uretim_verileri=initial_uretim_verileri, mod='yaz')
    if not initial_write_ok:
        print("HATA: Test için başlangıç durum dosyası oluşturulamadı.")
        sys.exit(1)
    print(f"-> Başlangıç dosyası oluşturuldu (Boyut: {os.path.getsize(state_filepath)} bytes).")

    # 4. Durumu oku ve tehlikeli değişikliği yap (veriyi küçült)
    son_adim_id, uretim_verileri = durum_yonetimi(config, mod='oku')
    if uretim_verileri is None:
        print("HATA: Test durumu dosyası geri okunamadı.")
        sys.exit(1)
    print("-> Büyük veri bloğu içeren durum dosyası okundu.")

    # Tehlikeli değişikliği yap
    del uretim_verileri['data']['large_data_block']
    print("-> 'large_data_block' durumdan silindi. Küçülmüş durum yazılmaya çalışılıyor...")

    # 5. Küçülmüş durumu yazmayı dene ve korumanın devreye girmesini bekle
    write_successful = durum_yonetimi(config, adim_id=son_adim_id, uretim_verileri=uretim_verileri, mod='yaz')

    # 6. Sonucu doğrula
    if not write_successful:
        print("\n[✓] TEST BAŞARILI: Veri küçülme koruması devreye girdi ve yazma işlemi engellendi.")
    else:
        print("\n[✗] TEST BAŞARISIZ: Küçülme koruması devreye girmedi ve veri kaybı yaşanabilirdi.")

    # Temizlik
    if os.path.exists(state_filepath):
        os.remove(state_filepath)
        print(f"-> Test durum dosyası '{state_filepath}' temizlendi.")

if __name__ == "__main__":
    main()