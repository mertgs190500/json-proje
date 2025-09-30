import json
import os

# --- Konfigürasyon ---
SOURCE_FILE = "uretim_cekirdek_v15_revised.json"
TARGET_FILE = "uretim_cekirdek_v17_nextgen.json"

# Helper function to load JSON file safely
def load_json_file(filename):
    if not os.path.exists(filename):
        print(f"HATA: Dosya bulunamadı: {filename}")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"HATA: Geçersiz JSON formatı: {filename}. Detaylar: {e}")
        return None

# Helper function to write JSON file
def write_json_file(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"BİLGİ: Dosya başarıyla yazıldı: {filename}")
    except Exception as e:
        print(f"HATA: Dosya yazılamadı: {filename}. Detaylar: {e}")

def run_corrections():
    print("--- Düzeltme İşlemi Başlatılıyor ---")
    data_v15 = load_json_file(SOURCE_FILE)
    data_v17 = load_json_file(TARGET_FILE)

    if data_v15 is None or data_v17 is None:
        print("KRİTİK HATA: Gerekli dosyalar yüklenemedi. İşlem durduruldu.")
        return

    corrections_made = 0

    # 1. /csv/similar_keywords_v2/v/required_columns_any_of eksik anahtarını düzelt
    try:
        if 'csv' in data_v17 and 'similar_keywords_v2' in data_v17['csv'] and 'v' in data_v17['csv']['similar_keywords_v2']:
            if 'required_columns_any_of' not in data_v17['csv']['similar_keywords_v2']['v']:
                source_val = data_v15.get('csv', {}).get('similar_keywords_v2', {}).get('v', {}).get('required_columns_any_of')
                if source_val is not None:
                    data_v17['csv']['similar_keywords_v2']['v']['required_columns_any_of'] = source_val
                    print("DÜZELTME: /csv/similar_keywords_v2/v/required_columns_any_of eklendi.")
                    corrections_made += 1
    except Exception as e:
        print(f"HATA (required_columns_any_of): {e}")

    # 2. /pl/audit/diff içindeki type mismatch'leri düzelt
    try:
        if 'pl' in data_v17 and 'audit' in data_v17['pl'] and 'diff' in data_v17['pl']['audit']:
             if isinstance(data_v17['pl']['audit']['diff'], list) and len(data_v17['pl']['audit']['diff']) > 0:
                for i, item in enumerate(data_v17['pl']['audit']['diff']):
                     # paths_changed'i düzelt
                    if 'paths_changed' in item and isinstance(item['paths_changed'], list):
                        item['paths_changed'] = {} # Boş bir dict'e çeviriyoruz, v15'te böyle
                        print(f"DÜZELTME: /pl/audit/diff/{i}/paths_changed tipi list -> dict olarak düzeltildi.")
                        corrections_made += 1
    except Exception as e:
        print(f"HATA (pl/audit/diff): {e}")


    # 3. /run/s/7/rs tipi düzeltmesi
    try:
        if 'run' in data_v17 and 's' in data_v17['run'] and '7' in data_v17['run']['s'] and isinstance(data_v17['run']['s']['7'].get('rs'), list):
            data_v17['run']['s']['7']['rs'] = {}
            print("DÜZELTME: /run/s/7/rs tipi list -> dict olarak düzeltildi.")
            corrections_made += 1
    except Exception as e:
        print(f"HATA (run/s/7/rs): {e}")

    # 4. /workflow_patches/s/5a/rs tipi düzeltmesi
    try:
        if 'workflow_patches' in data_v17 and 's' in data_v17['workflow_patches'] and '5a' in data_v17['workflow_patches']['s'] and isinstance(data_v17['workflow_patches']['s']['5a'].get('rs'), list):
             data_v17['workflow_patches']['s']['5a']['rs'] = {}
             print("DÜZELTME: /workflow_patches/s/5a/rs tipi list -> dict olarak düzeltildi.")
             corrections_made += 1
    except Exception as e:
        print(f"HATA (workflow_patches/s/5a/rs): {e}")

    # 5. /_run_order/steps/1a/o tipi düzeltmesi
    try:
        if '_run_order' in data_v17 and 'steps' in data_v17['_run_order'] and '1a' in data_v17['_run_order']['steps'] and isinstance(data_v17['_run_order']['steps']['1a'].get('o'), list):
            data_v17['_run_order']['steps']['1a']['o'] = {}
            print("DÜZELTME: /_run_order/steps/1a/o tipi list -> dict olarak düzeltildi.")
            corrections_made += 1
    except Exception as e:
        print(f"HATA (_run_order/steps/1a/o): {e}")


    if corrections_made > 0:
        print(f"\nToplam {corrections_made} düzeltme yapıldı.")
        write_json_file(data_v17, TARGET_FILE)
    else:
        print("\nHiçbir düzeltme yapılmadı. Dosya güncel olabilir.")

    print("--- Düzeltme İşlemi Tamamlandı ---")

if __name__ == "__main__":
    run_corrections()