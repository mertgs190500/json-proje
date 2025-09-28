import json

def fix_json_file(filepath):
    # Dosyayı oku
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Gerekli değişiklikleri yap
    # Adım 7'nin bağımlılığını ve adını güncelle
    if '7' in data.get('pl', {}).get('audit', {}).get('steps_snapshots', [{}])[0].get('s', {}):
        step_7 = data['pl']['audit']['steps_snapshots'][0]['s']['7']
        step_7['requires'] = ["6b"]
        step_7['n'] = "Rakip Analizi & Ads Çekirdeği"

        # run_order içindeki tanımı da güncelle (eğer varsa)
        if '7' in data.get('run', {}).get('s', {}):
             data['run']['s']['7']['n'] = "Rakip Analizi & Ads Çekirdeği"


    # Diğer bozuk bağımlılıkları düzelt
    # Adım 8a
    if '8a' in data.get('pl', {}).get('audit', {}).get('steps_snapshots', [{}])[0].get('s', {}):
        data['pl']['audit']['steps_snapshots'][0]['s']['8a']['requires'] = ["8"]

    # Adım 9
    if '9' in data.get('pl', {}).get('audit', {}).get('steps_snapshots', [{}])[0].get('s', {}):
        data['pl']['audit']['steps_snapshots'][0]['s']['9']['requires'] = ["8C"]


    # Dosyayı yeni haliyle yaz
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4) # İnsan tarafından okunabilir formatta yaz

    print(f"'{filepath}' dosyası başarıyla güncellendi.")

if __name__ == '__main__':
    fix_json_file('uretim_cekirdek_v14_strategic.json')