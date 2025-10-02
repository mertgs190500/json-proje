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

def compare_structures(ref_item, target_item, discrepancies, path=''):
    """Recursively compares the structure of two JSON objects (dicts or lists)."""
    # Compare dictionaries
    if isinstance(ref_item, dict) and isinstance(target_item, dict):
        for key, ref_value in ref_item.items():
            current_path = f"{path}.{key}" if path else key
            if key not in target_item:
                discrepancies.append(f"Eksik anahtar: '{current_path}'")
            else:
                target_value = target_item[key]
                if type(ref_value) != type(target_value):
                    discrepancies.append(f"Tip uyuşmazlığı: '{current_path}'. Referans: {type(ref_value).__name__}, Hedef: {type(target_value).__name__}")
                elif isinstance(ref_value, (dict, list)):
                    compare_structures(ref_value, target_value, discrepancies, path=current_path)
    # Compare lists
    elif isinstance(ref_item, list) and isinstance(target_item, list):
        # We only compare structure recursively if list items are dicts.
        # This check is simplified; it assumes list structures are similar if types match.
        for i, ref_list_item in enumerate(ref_item):
            # If the target list is shorter, we can't compare.
            if i >= len(target_item):
                discrepancies.append(f"Hedef liste '{path}' referanstan daha kısa.")
                break

            target_list_item = target_item[i]
            current_path = f"{path}[{i}]"

            if type(ref_list_item) != type(target_list_item):
                 discrepancies.append(f"Liste öğesi tip uyuşmazlığı: '{current_path}'. Referans: {type(ref_list_item).__name__}, Hedef: {type(target_list_item).__name__}")
            elif isinstance(ref_list_item, (dict, list)):
                compare_structures(ref_list_item, target_list_item, discrepancies, path=current_path)


def main():
    """Main function to load files and run the comparison."""
    ref_file = 'uretim_cekirdek_v15_revised.json'
    target_file = 'finalv1.json'

    print(f"Referans dosya yükleniyor: {ref_file}")
    ref_data = load_json_file(ref_file)

    print(f"Hedef dosya yükleniyor: {target_file}")
    target_data = load_json_file(target_file)

    if ref_data is None or target_data is None:
        print("Dosya yükleme hatası nedeniyle karşılaştırma yapılamadı.")
        return

    discrepancies = []
    print("\nİki dosya arasında yapısal karşılaştırma başlatılıyor...")
    compare_structures(ref_data, target_data, discrepancies)

    if not discrepancies:
        print("\n--- RAPOR ---")
        print("İki dosya arasında yapısal bir veri kaybı tespit edilmedi.")
    else:
        print("\n--- RAPOR ---")
        print("Aşağıdaki uyuşmazlıklar tespit edildi:")
        for issue in discrepancies:
            print(f"- {issue}")

if __name__ == "__main__":
    main()