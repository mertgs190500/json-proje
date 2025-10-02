import json
import sys
import collections.abc
import jsonpatch

def deep_update(d, u):
    """
    Recursively update a dictionary.
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping) and isinstance(d.get(k), dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def get_v13_enhancements_as_value():
    """
    Returns the first set of enhancements as a single dictionary value
    to be merged into the base data.
    """
    # This combines the top-level keys and the 'wp.s' step modifications
    # into a single structure for a one-shot deep_update.
    return {
        "Workflow_Configuration": {
            "description": "Genel iş akışı yapılandırması ve otonomi ayarları (Soru 4).",
            "automation_level": "HIGH_AUTONOMY",
            "decision_making": "Gemini, analizlere dayanarak en yüksek SEO potansiyeline sahip seçenekleri otonom olarak seçer ve karar gerekçesini raporlar.",
            "mandatory_user_interaction": ["Step_0_Initial_Input", "Adim_Gorsel_Yukleme", "Adim_CSV_Yukleme_Manager", "Adim_16_Record_Type_Select"],
            "halt_policy": "CRITICAL_FAILURE_OR_FINAL_CHECKPOINT"
        },
        "Module_Seasonal_Timeline_Manager": { "description": "Özel günler için dinamik içerik ve süreç yönetimi (Soru 8).", "type": "Conditional_Module", "configuration": { "events": [{"name": "Christmas", "date": "12-25", "lead_time_days": 45}, {"name": "Valentine's Day", "date": "02-14", "lead_time_days": 30}], "actions": ["INJECT_SEASONAL_KEYWORDS", "ACTIVATE_SHIPPING_DEADLINES_MESSAGING"]}},
        "Module_CSV_Analiz_Stratejisi": { "description": "CSV verilerinin stratejik SEO perspektifiyle işlenmesi (Soru 12).", "strategy": { "quality_intent_weighting": { "description": "(12.B.1) Kalite ve Niyet Ağırlıklandırması: LQS ve Conversion Rate metriklerine göre anahtar kelimeleri ağırlıklandırır.", "parameters": {"lqs_priority": True, "cr_priority": True}}, "rising_trend_detection": { "description": "(12.B.2) Yükselen Trend Tespiti: 'Listing Age' metriğini kullanarak pazarda yeni popülerleşen trendleri tespit eder.", "parameters": {"max_age_for_trend": 90}}, "market_requirements_analysis": { "description": "(12.B.3) Pazar Gereksinimleri Analizi: Başarılı rakiplerin 'Video' ve 'Free Shipping' sunma oranlarını analiz eder ve raporlar."}}},
        "Module_Diversification_Policies": { "description": "Benzer ürün analizlerinde tekrara düşmeyi önlemek için uygulanan politikalar (Soru 13).", "seed_diversification": { "applied_to": ["Adim_1b", "Adim_3a"], "description": "(13.1) Başlangıç Tohumlarını Çeşitlendirme: Ana ürün tanımına sinonimler, long-tail varyasyonlar ekleyerek başlangıç tohumlarını çeşitlendirir."}, "lateral_expansion": { "applied_to": ["Adim_3a"], "description": "(13.2) Yanal Anahtar Kelime Genişletmesi: Sadece doğrudan ilgili kelimeleri değil, kullanım senaryoları veya farklı nişlerle ilgili kelimeleri araştırır."}, "competitor_cooling_policy": { "applied_to": ["Adim_5c"], "description": "(13.3) Rakip Soğutma Politikası: Son analizlerde baskın çıkan rakiplerin verilerinin ağırlığını geçici olarak düşürür.", "parameters": {"cooling_duration_days": 30, "enabled": True}}},
        "wp": {"s": {
            "1a": {"description": "Yüklenen görsellerin derinlemesine yapay zeka analizi.", "processes": {"semantic_aesthetic_analysis": {"description": "(Soru 5.1) Derin Semantik ve Estetik Analiz: Stil, materyal, renk paleti ve estetik unsurları analiz eder.", "enabled": True}, "ocr_extraction": {"description": "(Soru 5.2) Metin Tanıma (OCR): Görsel üzerindeki metinleri tanımlar ve çıkarır.", "enabled": True}, "auto_alt_text_generation": {"description": "(Soru 5.3) Otomatik Alt-Text Üretimi (Kritik SEO): Semantik analiz çıktılarını kullanarak SEO uyumlu Alt-Text üretir.", "enabled": True}, "direct_seo_injection": {"description": "(Soru 5.4) Doğrudan SEO Enjeksiyonu: Görsel analizden elde edilen içgörüleri (keywords) doğrudan anahtar kelime havuzuna enjekte eder.", "enabled": True}}},
            "10": {"rules_engine": {"dynamic_material_prioritization": {"description": "(Soru 6) Varsayılan materyali (Step 0) kullanmak yerine, Adım 8'deki Pazar Analizi verilerine göre en popüler materyali (örn. 14k vs 18k) başlıkta önceliklendirir.", "data_source": "Adim_8_Pazar_Analizi_Raporu", "enabled": True}, "optional_variant_inclusion": {"description": "(Soru 6) Başlıkta yer almayan diğer 'k' seçeneklerini, karakter limiti izin veriyorsa, başlığın sonuna opsiyonel olarak (örn: '... | 10k 18k Available') ekler.", "enabled": True}, "draft_evolution_and_refinement": {"description": "(Soru 9) Adım 3b/c'deki taslak başlığı temel alır ancak Adım 8'de belirlenen en yüksek niyetli anahtar kelimelerle yeniden yapılandırır ve çeşitlendirir.", "enabled": True}}},
            "11": {"parameters": {"target_length": "EXTENDED (2000+ characters)"}, "content_modules": {"usage_scenarios_and_storytelling": {"description": "(Soru 7.A) Açıklama İçeriği ve Derinliği: Kullanım alanları, hediye senaryoları, stil önerileri gibi derinlikli içerik ekler.", "required": True}, "production_process_clarification": {"description": "(Soru 7.B) 'Sipariş Üzerine Üretim' Algısı (1-3 Gün): Bu sürenin stoklama değil, kişiye özel üretim/zanaatkarlık olduğunu profesyonelce vurgular.", "messaging_template": "Meticulously handcrafted just for you. Your order will be ready for shipping in 1-3 business days, ensuring the highest quality and attention to detail."}, "seasonal_content_injection": {"description": "(Soru 8) Module_Seasonal_Timeline_Manager'dan gelen verilerle sezonsal mesajları (örn. son sipariş tarihleri) ekler.", "required": False}}},
            "9b": {"description": "(Soru 10.A) Ürün Kategorisi: En uygun Etsy kategori hiyerarşisini otonom olarak belirler.", "method": "AI_TAXONOMY_MAPPING", "inputs": ["Gorsel_Analiz_Ciktilari", "Taslak_SEO_Paketi", "Pazar_Analizi_Raporu"], "outputs": ["Etsy_Category_ID", "Etsy_Category_Path"]},
            "17": {"description": "(Soru 10.C) Export İçeriği: Nihai listeleme verilerini dışa aktarır.", "formats": ["CSV", "XLSX", "JSON"], "content_schema_enhancements": {"Etsy_Category_ID": {"source": "Adim_9b_Otomatik_Kategorizasyon"}, "Etsy_Category_Path": {"source": "Adim_9b_Otomatik_Kategorizasyon"}, "Image_Alt_Texts": {"source": "Adim_1_Gorsel_Analiz_Enhanced"}, "Materials_List_Detailed": {}, "Production_Time_Profile": {}, "Shipping_Profile_ID": {}}},
            "7": {"analysis_focus": {"sponsored_listing_strategy": {"description": "(Grup 3) Rakiplerin reklam çıktığı ürünleri (Promoted Listings) ve stratejilerini tespit eder. Bu alanları yüksek niyetli kabul eder."}, "pricing_and_offer_benchmarking": {"description": "(Grup 3) Rakiplerin fiyatlandırma stratejileri, indirim oranları ve kargo tekliflerini sistematik olarak analiz eder."}, "keyword_gap_analysis_ads": {"description": "(Grup 3) Rakiplerin zayıf olduğu veya hedeflemediği anahtar kelime boşluklarını (Gap Analysis) tespit eder."}}},
            "14": {"evaluation_metrics": {"thematic_cohesion_analysis": {"description": "(Grup 3) Anlamsal Bütünlük: Başlık, etiketler ve açıklamanın anlamsal olarak ne kadar uyumlu olduğunu kontrol eder (Semantic Consistency)."}, "intent_alignment_score": {"description": "(Grup 3) Tüm SEO elemanlarının aynı kullanıcı niyetini hedefleyip hedeflemediğini puanlar."}}},
            "15": {"quality_checks": {"readability_score_assessment": {"description": "(Grup 3) Açıklama metninin okunabilirliğini değerlendirir ve hedef kitleye uygunluğunu kontrol eder."}, "over_optimization_detector": {"description": "(Grup 3) Aşırı anahtar kelime kullanımı (keyword stuffing) riskini analiz eder."}}},
            "16": {"processes": {"data_integrity_validation": {"description": "(Grup 3) Birleştirme öncesi tüm gerekli alanların (SKU, Fiyat, Varyasyonlar, Kategori) dolu ve geçerli formatta olduğunu doğrular."}}},
            "seo_package": {"final_checks": {"goal_alignment_verification": {"description": "(Grup 3) Nihai SEO paketinin başlangıç hedefleri ve Pazar Analizi sonuçlarıyla uyumluluğunun nihai doğrulaması."}, "uniqueness_and_plagiarism_check": {"description": "(Grup 3) Oluşturulan metinlerin özgünlüğünü ve mevcut listelemelerimizle benzerliğini kontrol eder."}}},
            "18": {"evaluations": {"holistic_seo_assessment": {"description": "(Soru 14) Bütünsel SEO Değerlendirmesi: Tüm bileşenlerin (Başlık, Etiket, Açıklama, Alt-Text) uyumunu değerlendirir ve Genel SEO Skoru atar."}, "marketplace_compliance_check": {"description": "(Soru 14) Pazar Yeri Gereksinimleri Kontrolü: Etsy kurallarına (limitler, yasaklı kelimeler) uygunluğu kontrol eder.", "platform": "Etsy"}, "simulation_and_preview": {"description": "(Soru 14) Simülasyon ve Önizleme: Listelemenin arama sonuçlarında (SERP Snippet) nasıl görüneceğinin simülasyonunu sunar."}}},
            "19": {"trigger": "30_DAYS_POST_PUBLISH", "processes": {"data_integration": {"description": "(Soru 15.1) Veri Entegrasyonu: Etsy API veya CSV üzerinden güncel performans verilerini (Views, Orders, Search Queries) entegre eder."}, "winner_loser_analysis": {"description": "(Soru 15.2) 'Kazanan' (trafik getiren) ve 'Kaybeden' (performans göstermeyen) anahtar kelimelerin analizi."}, "automated_ab_test_planning": {"description": "(Soru 15.3) Otomatik A/B Testi Planlaması: Performansı artırmak için otomatik test senaryoları (örn: Ana görsel değişikliği, Başlık V2) planlar."}}},
            "20": {"features": {"detailed_changelog_generation": {"description": "(Soru 16.1) Değişiklik Günlüğü (Changelog): Her güncellemede neyin, neden değiştirildiğini otomatik olarak kaydeder."}, "performance_tagging": {"description": "(Soru 16.2) Performans Etiketleme: Her versiyonu, ilgili performans metrikleriyle (örn: V1.2 - CVR %2.1) etiketler."}, "automated_rollback_trigger": {"description": "(Soru 16.3) Otomatik Geri Alma Kuralı: Yeni sürüm %20'den fazla performans düşüşü yaşarsa (72 saat içinde), sistem uyarı verir ve önceki stabil sürüme geri dönmeyi önerir.", "condition": "Performance_Drop > 20%", "action": "ALERT_AND_SUGGEST_ROLLBACK"}}}
        }}
    }

def convert_to_json_patch(instructions, base_doc):
    """Converts the user's custom instructions into a standard JSON Patch list."""
    patch = []

    # Handle direct top-level merges as 'add' operations
    if 'value' in instructions and isinstance(instructions['value'], dict):
        for key, value in instructions['value'].items():
            patch.append({'op': 'add', 'path': f'/{key}', 'value': value})

    for op_group in instructions.get('operations', []):
        for action in op_group.get('actions', []):
            op = {}
            path = action['path']
            value = action.get('value')

            if action['action'] in ['add_or_merge', 'update_value', 'add_if_not_exists']:
                # For simplicity, we treat these as 'add' or 'replace'.
                # jsonpatch handles adding to dicts.
                # We'll use a simple check to see if the path exists.
                try:
                    jsonpatch.JsonPointer(path).resolve(base_doc)
                    op['op'] = 'replace'
                except jsonpatch.JsonPointerException:
                    op['op'] = 'add'
                op['path'] = path
                op['value'] = value
                patch.append(op)

            elif action['action'] == 'append_to_list':
                # JSON Patch standard for appending to a list is using '/-'
                op['op'] = 'add'
                op['path'] = f"{path}/-"
                op['value'] = value
                patch.append(op)

    return patch

def main():
    base_file = 'uretim_cekirdek_v13_revised.json'
    v14_instructions_file = 'v14_instructions.json'

    try:
        with open(base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load base file '{base_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Pass 1: Apply v13 enhancements ---
    print("Applying v13 enhancements...")
    v13_enhancements = get_v13_enhancements_as_value()
    deep_update(data, v13_enhancements)
    print("v13 enhancements applied.")

    # --- Pass 2: Apply v14 enhancements using jsonpatch ---
    print("\nApplying v14 strategic enhancements...")
    try:
        with open(v14_instructions_file, 'r', encoding='utf-8') as f:
            v14_instructions = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load v14 instructions file '{v14_instructions_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create necessary parent paths before generating the patch
    for op_group in v14_instructions.get('operations', []):
        for action in op_group.get('actions', []):
            try:
                get_parent_and_key(data, action['path'])
            except Exception as e:
                print(f"  - Pre-flight check failed for path '{action['path']}'. Error: {e}", file=sys.stderr)

    # Now convert and apply the patch
    try:
        patch_ops = convert_to_json_patch(v14_instructions, data)
        jsonpatch.apply_patch(data, patch_ops, inplace=True)
        print("v14 enhancements applied successfully.")
    except Exception as e:
        print(f"FATAL: Could not apply JSON patch. Error: {e}", file=sys.stderr)
        # print("Generated patch:", json.dumps(patch_ops, indent=2))
        sys.exit(1)


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