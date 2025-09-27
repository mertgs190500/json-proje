import json
import sys
import collections.abc

def deep_update(d, u):
    """
    Recursively update a dictionary. If the existing value is not a dict, it's overwritten.
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping) and isinstance(d.get(k), dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def get_parent_and_key(doc, path):
    """
    Given a JSON path, traverses the document and returns the direct parent
    element and the final key/part of the path.
    Creates nested dictionaries if they do not exist along the path.
    """
    if not path.startswith('/'):
        raise ValueError(f"Invalid path format: '{path}'. Must start with '/'.")

    parts = path.strip('/').split('/')
    if not parts or parts == ['']:
        return None, None # Cannot operate on the root itself.

    current_level = doc
    # Traverse to the parent dictionary, creating nested dicts as needed.
    for part in parts[:-1]:
        if not isinstance(current_level, dict):
            raise TypeError(f"Path traversal failed. Element at path prefix is not a dictionary.")
        current_level = current_level.setdefault(part, {})

    return current_level, parts[-1]


def apply_operation(doc, operation):
    """
    Applies a single operation from the instructions file to the document.
    """
    action = operation['action']
    path = operation['path']
    value = operation.get('value')

    parent, key = get_parent_and_key(doc, path)
    if parent is None:
        print(f"  - SKIPPING: Cannot get parent for path '{path}'")
        return False

    if action == 'add_or_merge':
        existing_value = parent.get(key)
        if isinstance(existing_value, dict) and isinstance(value, dict):
             deep_update(existing_value, value)
        else:
            parent[key] = value

    elif action == 'update_value':
        parent[key] = value

    elif action == 'add_if_not_exists':
        # This action has special logic for lists of objects
        target_container = parent.get(key)
        if isinstance(target_container, list):
            # If the target is a list, check for existence by 'id' before appending
            item_id = value.get('id')
            if item_id is None:
                # If no ID, just append if not a complete duplicate
                if value not in target_container:
                    target_container.append(value)
            else:
                # If there's an ID, check if any item in the list has that ID
                is_present = any(isinstance(item, dict) and item.get('id') == item_id for item in target_container)
                if not is_present:
                    target_container.append(value)
        else:
            # Default behavior for dicts: add only if key is missing
            parent.setdefault(key, value)


    elif action == 'append_to_list':
        target_list = parent.setdefault(key, [])
        if not isinstance(target_list, list):
            print(f"  - ERROR: Target for append is not a list at path '{path}'", file=sys.stderr)
            return False
        if value not in target_list:
            target_list.append(value)

    else:
        print(f"  - WARNING: Unknown action type '{action}'", file=sys.stderr)
        return False

    return True


def apply_instruction_set(base_data, instructions):
    """Applies a full set of instructions to the base data."""
    print(f"\nProcessing instruction set: {instructions.get('description', 'N/A')}")

    # Handle direct top-level merges if specified
    if 'value' in instructions and isinstance(instructions['value'], dict):
        deep_update(base_data, instructions['value'])

    # Handle operation-based enhancements
    for op_group in instructions.get('operations', []):
        print(f"  Processing Group: {op_group['group']}")
        for action in op_group.get('actions', []):
            try:
                success = apply_operation(base_data, action)
                if success:
                    print(f"    - Applied '{action['action']}' to '{action['path']}'")
            except Exception as e:
                print(f"    - FAILED action for path '{action['path']}'. Error: {e}", file=sys.stderr)


def get_v13_enhancements():
    """Returns the first set of enhancements as an instructions dictionary."""
    return {
        "description": "Initial v13 enhancements (simulated)",
        "value": {
            "Workflow_Configuration": {
              "description": "Genel iş akışı yapılandırması ve otonomi ayarları (Soru 4).",
              "automation_level": "HIGH_AUTONOMY",
              "decision_making": "Gemini, analizlere dayanarak en yüksek SEO potansiyeline sahip seçenekleri otonom olarak seçer ve karar gerekçesini raporlar.",
              "mandatory_user_interaction": ["Step_0_Initial_Input", "Adim_Gorsel_Yukleme", "Adim_CSV_Yukleme_Manager", "Adim_16_Record_Type_Select"],
              "halt_policy": "CRITICAL_FAILURE_OR_FINAL_CHECKPOINT"
            },
            "Module_Seasonal_Timeline_Manager": { "description": "Özel günler için dinamik içerik ve süreç yönetimi (Soru 8).", "type": "Conditional_Module", "configuration": { "events": [{"name": "Christmas", "date": "12-25", "lead_time_days": 45}, {"name": "Valentine's Day", "date": "02-14", "lead_time_days": 30}], "actions": ["INJECT_SEASONAL_KEYWORDS", "ACTIVATE_SHIPPING_DEADLINES_MESSAGING"]}},
            "Module_CSV_Analiz_Stratejisi": { "description": "CSV verilerinin stratejik SEO perspektifiyle işlenmesi (Soru 12).", "strategy": { "quality_intent_weighting": { "description": "(12.B.1) Kalite ve Niyet Ağırlıklandırması: LQS ve Conversion Rate metriklerine göre anahtar kelimeleri ağırlıklandırır.", "parameters": {"lqs_priority": True, "cr_priority": True}}, "rising_trend_detection": { "description": "(12.B.2) Yükselen Trend Tespiti: 'Listing Age' metriğini kullanarak pazarda yeni popülerleşen trendleri tespit eder.", "parameters": {"max_age_for_trend": 90}}, "market_requirements_analysis": { "description": "(12.B.3) Pazar Gereksinimleri Analizi: Başarılı rakiplerin 'Video' ve 'Free Shipping' sunma oranlarını analiz eder ve raporlar."}}},
            "Module_Diversification_Policies": { "description": "Benzer ürün analizlerinde tekrara düşmeyi önlemek için uygulanan politikalar (Soru 13).", "seed_diversification": { "applied_to": ["Adim_1b", "Adim_3a"], "description": "(13.1) Başlangıç Tohumlarını Çeşitlendirme: Ana ürün tanımına sinonimler, long-tail varyasyonlar ekleyerek başlangıç tohumlarını çeşitlendirir."}, "lateral_expansion": { "applied_to": ["Adim_3a"], "description": "(13.2) Yanal Anahtar Kelime Genişletmesi: Sadece doğrudan ilgili kelimeleri değil, kullanım senaryoları veya farklı nişlerle ilgili kelimeleri araştırır."}, "competitor_cooling_policy": { "applied_to": ["Adim_5c"], "description": "(13.3) Rakip Soğutma Politikası: Son analizlerde baskın çıkan rakiplerin verilerinin ağırlığını geçici olarak düşürür.", "parameters": {"cooling_duration_days": 30, "enabled": True}}}
        },
        "operations": [{ "group": "Step Enhancements for v13", "actions": [
            {"action": "add_or_merge", "path": "/wp/s/1a", "value": {"description": "Yüklenen görsellerin derinlemesine yapay zeka analizi.", "processes": {"semantic_aesthetic_analysis": {"description": "(Soru 5.1) Derin Semantik ve Estetik Analiz: Stil, materyal, renk paleti ve estetik unsurları analiz eder.", "enabled": True}, "ocr_extraction": {"description": "(Soru 5.2) Metin Tanıma (OCR): Görsel üzerindeki metinleri tanımlar ve çıkarır.", "enabled": True}, "auto_alt_text_generation": {"description": "(Soru 5.3) Otomatik Alt-Text Üretimi (Kritik SEO): Semantik analiz çıktılarını kullanarak SEO uyumlu Alt-Text üretir.", "enabled": True}, "direct_seo_injection": {"description": "(Soru 5.4) Doğrudan SEO Enjeksiyonu: Görsel analizden elde edilen içgörüleri (keywords) doğrudan anahtar kelime havuzuna enjekte eder.", "enabled": True}}}},
            {"action": "add_or_merge", "path": "/wp/s/10", "value": {"rules_engine": {"dynamic_material_prioritization": {"description": "(Soru 6) Varsayılan materyali (Step 0) kullanmak yerine, Adım 8'deki Pazar Analizi verilerine göre en popüler materyali (örn. 14k vs 18k) başlıkta önceliklendirir.", "data_source": "Adim_8_Pazar_Analizi_Raporu", "enabled": True}, "optional_variant_inclusion": {"description": "(Soru 6) Başlıkta yer almayan diğer 'k' seçeneklerini, karakter limiti izin veriyorsa, başlığın sonuna opsiyonel olarak (örn: '... | 10k 18k Available') ekler.", "enabled": True}, "draft_evolution_and_refinement": {"description": "(Soru 9) Adım 3b/c'deki taslak başlığı temel alır ancak Adım 8'de belirlenen en yüksek niyetli anahtar kelimelerle yeniden yapılandırır ve çeşitlendirir.", "enabled": True}}}},
            {"action": "add_or_merge", "path": "/wp/s/11", "value": {"parameters": {"target_length": "EXTENDED (2000+ characters)"}, "content_modules": {"usage_scenarios_and_storytelling": {"description": "(Soru 7.A) Açıklama İçeriği ve Derinliği: Kullanım alanları, hediye senaryoları, stil önerileri gibi derinlikli içerik ekler.", "required": True}, "production_process_clarification": {"description": "(Soru 7.B) 'Sipariş Üzerine Üretim' Algısı (1-3 Gün): Bu sürenin stoklama değil, kişiye özel üretim/zanaatkarlık olduğunu profesyonelce vurgular.", "messaging_template": "Meticulously handcrafted just for you. Your order will be ready for shipping in 1-3 business days, ensuring the highest quality and attention to detail."}, "seasonal_content_injection": {"description": "(Soru 8) Module_Seasonal_Timeline_Manager'dan gelen verilerle sezonsal mesajları (örn. son sipariş tarihleri) ekler.", "required": False}}}},
            {"action": "add_or_merge", "path": "/wp/s/9b", "value": {"description": "(Soru 10.A) Ürün Kategorisi: En uygun Etsy kategori hiyerarşisini otonom olarak belirler.", "method": "AI_TAXONOMY_MAPPING", "inputs": ["Gorsel_Analiz_Ciktilari", "Taslak_SEO_Paketi", "Pazar_Analizi_Raporu"], "outputs": ["Etsy_Category_ID", "Etsy_Category_Path"]}},
            {"action": "add_or_merge", "path": "/wp/s/17", "value": {"description": "(Soru 10.C) Export İçeriği: Nihai listeleme verilerini dışa aktarır.", "formats": ["CSV", "XLSX", "JSON"], "content_schema_enhancements": {"Etsy_Category_ID": {"source": "Adim_9b_Otomatik_Kategorizasyon"}, "Etsy_Category_Path": {"source": "Adim_9b_Otomatik_Kategorizasyon"}, "Image_Alt_Texts": {"source": "Adim_1_Gorsel_Analiz_Enhanced"}, "Materials_List_Detailed": {}, "Production_Time_Profile": {}, "Shipping_Profile_ID": {}}}},
            {"action": "add_or_merge", "path": "/wp/s/7", "value": {"analysis_focus": {"sponsored_listing_strategy": {"description": "(Grup 3) Rakiplerin reklam çıktığı ürünleri (Promoted Listings) ve stratejilerini tespit eder. Bu alanları yüksek niyetli kabul eder."}, "pricing_and_offer_benchmarking": {"description": "(Grup 3) Rakiplerin fiyatlandırma stratejileri, indirim oranları ve kargo tekliflerini sistematik olarak analiz eder."}, "keyword_gap_analysis_ads": {"description": "(Grup 3) Rakiplerin zayıf olduğu veya hedeflemediği anahtar kelime boşluklarını (Gap Analysis) tespit eder."}}}},
            {"action": "add_or_merge", "path": "/wp/s/14", "value": {"evaluation_metrics": {"thematic_cohesion_analysis": {"description": "(Grup 3) Anlamsal Bütünlük: Başlık, etiketler ve açıklamanın anlamsal olarak ne kadar uyumlu olduğunu kontrol eder (Semantic Consistency)."}, "intent_alignment_score": {"description": "(Grup 3) Tüm SEO elemanlarının aynı kullanıcı niyetini hedefleyip hedeflemediğini puanlar."}}}},
            {"action": "add_or_merge", "path": "/wp/s/15", "value": {"quality_checks": {"readability_score_assessment": {"description": "(Grup 3) Açıklama metninin okunabilirliğini değerlendirir ve hedef kitleye uygunluğunu kontrol eder."}, "over_optimization_detector": {"description": "(Grup 3) Aşırı anahtar kelime kullanımı (keyword stuffing) riskini analiz eder."}}}},
            {"action": "add_or_merge", "path": "/wp/s/16", "value": {"processes": {"data_integrity_validation": {"description": "(Grup 3) Birleştirme öncesi tüm gerekli alanların (SKU, Fiyat, Varyasyonlar, Kategori) dolu ve geçerli formatta olduğunu doğrular."}}}},
            {"action": "add_or_merge", "path": "/wp/s/seo_package", "value": {"final_checks": {"goal_alignment_verification": {"description": "(Grup 3) Nihai SEO paketinin başlangıç hedefleri ve Pazar Analizi sonuçlarıyla uyumluluğunun nihai doğrulaması."}, "uniqueness_and_plagiarism_check": {"description": "(Grup 3) Oluşturulan metinlerin özgünlüğünü ve mevcut listelemelerimizle benzerliğini kontrol eder."}}}},
            {"action": "add_or_merge", "path": "/wp/s/18", "value": {"evaluations": {"holistic_seo_assessment": {"description": "(Soru 14) Bütünsel SEO Değerlendirmesi: Tüm bileşenlerin (Başlık, Etiket, Açıklama, Alt-Text) uyumunu değerlendirir ve Genel SEO Skoru atar."}, "marketplace_compliance_check": {"description": "(Soru 14) Pazar Yeri Gereksinimleri Kontrolü: Etsy kurallarına (limitler, yasaklı kelimeler) uygunluğu kontrol eder.", "platform": "Etsy"}, "simulation_and_preview": {"description": "(Soru 14) Simülasyon ve Önizleme: Listelemenin arama sonuçlarında (SERP Snippet) nasıl görüneceğinin simülasyonunu sunar."}}}},
            {"action": "add_or_merge", "path": "/wp/s/19", "value": {"trigger": "30_DAYS_POST_PUBLISH", "processes": {"data_integration": {"description": "(Soru 15.1) Veri Entegrasyonu: Etsy API veya CSV üzerinden güncel performans verilerini (Views, Orders, Search Queries) entegre eder."}, "winner_loser_analysis": {"description": "(Soru 15.2) 'Kazanan' (trafik getiren) ve 'Kaybeden' (performans göstermeyen) anahtar kelimelerin analizi."}, "automated_ab_test_planning": {"description": "(Soru 15.3) Otomatik A/B Testi Planlaması: Performansı artırmak için otomatik test senaryoları (örn: Ana görsel değişikliği, Başlık V2) planlar."}}}},
            {"action": "add_or_merge", "path": "/wp/s/20", "value": {"features": {"detailed_changelog_generation": {"description": "(Soru 16.1) Değişiklik Günlüğü (Changelog): Her güncellemede neyin, neden değiştirildiğini otomatik olarak kaydeder."}, "performance_tagging": {"description": "(Soru 16.2) Performans Etiketleme: Her versiyonu, ilgili performans metrikleriyle (örn: V1.2 - CVR %2.1) etiketler."}, "automated_rollback_trigger": {"description": "(Soru 16.3) Otomatik Geri Alma Kuralı: Yeni sürüm %20'den fazla performans düşüşü yaşarsa (72 saat içinde), sistem uyarı verir ve önceki stabil sürüme geri dönmeyi önerir.", "condition": "Performance_Drop > 20%", "action": "ALERT_AND_SUGGEST_ROLLBACK"}}}}
        ]}]
    }

def main():
    base_file = 'uretim_cekirdek_v13_revised.json'
    v14_instructions_file = 'v14_instructions.json'

    try:
        with open(base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load base file '{base_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Apply v13 enhancements first
    v13_instructions = get_v13_enhancements()
    apply_instruction_set(data, v13_instructions)

    # Then, apply v14 enhancements
    try:
        with open(v14_instructions_file, 'r', encoding='utf-8') as f:
            v14_instructions = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load v14 instructions file '{v14_instructions_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    apply_instruction_set(data, v14_instructions)

    output_file = f"uretim_cekirdek_{v14_instructions.get('new_version', 'final')}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"\nSuccessfully created final configuration file: {output_file}")
    except Exception as e:
        print(f"FATAL: Could not write output file '{output_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()