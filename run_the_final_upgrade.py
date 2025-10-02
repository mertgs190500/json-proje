# run_the_final_upgrade.py (v5 - SyntaxError Düzeltilmiş Versiyon)

import json
import requests
from collections import OrderedDict

# --- KONFİGÜRASYON ---
SOURCE_URL = 'https://raw.githubusercontent.com/mertgs190500/json-proje/refs/heads/main/uretim_cekirdek_v15_revised.json'
LOCAL_SOURCE_FILE = 'uretim_cekirdek_v15_revised.json'
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
        print(f"HATA: İndirilen kaynak dosya bulunamadı: {filename}")
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

# --- DEĞİŞİKLİK VERİLERİ (TAM VE EKSİKSİZ) ---

changes_v16 = {
    "_runtime": {"kb": {"description": "Persistent Knowledge Base for strategic learning, market caching, and competitor tracking.", "strategic_learnings": [], "competitor_cooldown": {}, "market_cache": {"last_updated": None, "price_analysis": {}, "visual_trends": {}}}, "seasonal_windows": {"valentines_day": {"start_month": 1, "end_month": 2, "themes": ["valentines gift", "romantic gift"]}, "mothers_day": {"start_month": 4, "end_month": 5, "themes": ["mothers day gift", "gift for mom"]}, "holiday_season": {"start_month": 11, "end_month": 12, "themes": ["christmas gift", "holiday present"]}}},
    "shop_profile": {"brand_voice": {"tone": "Elegant, professional, trustworthy", "keywords": ["handcrafted", "quality", "timeless", "minimalist"], "style": "Clear, concise, benefit-oriented."}},
    "run": {"s": {"1": {"requires": ["00"]}, "0": {"requires": ["1a"]}, "1b": {"requires": ["0"]}, "0a": {"o": {"api_health_status": None, "dependency_report": None, "schema_validation_status": None}}, "00": {"i": {"kb_ref": "[REF to /_runtime/kb/]"}, "rs": ["Tüm aktif adımların girdi (requires) ve çıktı (o) zincirini simüle et. Kopukluk varsa BLOCKER olarak raporla."], "o": {"system_health_report": {"blockers": [], "warnings": [], "info": []}}}, "1a": {"rs": ["Her görsel için SEO uyumlu alt_text üret.", "Görselden stil/malzeme çıkarımı yap (visual_attribute_suggestions, visual_tag_suggestions).", "CTR potansiyeline göre görselleri puanla (thumbnail_score) (A/B testi için)."], "o": {"visual_attribute_suggestions": [], "visual_tag_suggestions": [], "media": {"manifest": {"alt_text": None, "thumbnail_score": None}}}}, "0": {"i": {"visual_analysis_outputs": "[REF to 1a.outputs]", "market_cache_ref": "[REF to /_runtime/kb/market_cache]"}, "rs": ["Görsel Tutarlılık: 1a'dan gelen görsel çıkarımlar ile product_record metinlerini karşılaştır ve uyar.", "Fiyat Etki Önizlemesi: market_cache varsa, girilen fiyatın pazar ortalamasına göre konumunu göster."]}, "1b": {"i": {"current_date_ref": "[REF to runtime.current_date]", "seasonal_windows_ref": "[REF to /_runtime/seasonal_windows]", "market_cache_ref": "[REF to /_runtime/kb/market_cache]"}, "rs": ["Tarihe göre sezonluk trendleri (Trend Focus) ve market_cache kullanarak rakip boşluklarını (Competitor Gap Focus) önceliklendir."]}, "5a": {"rs": ["Pazar fiyat istatistiklerini hesapla (market_price_analysis).", "Rakiplerin fotoğraf stratejilerini analiz et (visual_strategy_gaps)."], "o": {"market_price_analysis": {}, "visual_strategy_gaps": []}, "fl": {"post_action": "Write market_price_analysis to /_runtime/kb/market_cache"}}, "5c": {"i": {"cooldown_ref": "[REF to /_runtime/kb/competitor_cooldown]"}, "rs": ["Rakip Sağlamlık Puanı hesapla", "competitor_cooldown listesindeki rakiplere ceza puanı uygula (Soğutma)."], "fl": {"post_action": "Write selected competitors to /_runtime/kb/competitor_cooldown"}}, "3b": {"i": {"brand_voice_ref": "[REF to /shop_profile/brand_voice]"}, "rs": ["Üretilen metinlerin tonu /shop_profile/brand_voice ile tutarlı olmalıdır."]}, "10": {"rs": ["Farklı niyetlere (Örn: Özellik Odaklı, Hediye Odaklı) yönelik 2-3 başlık varyasyonu üret (A/B Test)."], "o": {"titles": {"variations": []}}}, "11": {"i": {"current_date_ref": "[REF to runtime.current_date]", "seasonal_windows_ref": "[REF to /_runtime/seasonal_windows]"}, "rs": ["Tarihe göre dinamik sezonluk içerik blokları ekle."]}, "8a": {"rs": ["Kampanya planı oluştur: Eşleşme Türü, Bütçe/Teklif stratejisi, Reklam Metni varyasyonları, Kitle Profili, A/B test senaryoları."], "o": {"ads_campaign_plan": {"groups": [], "budget_strategy": None, "ab_tests": []}}}, "8C": {"vlds": {"id": "CONFLICT_CHECK", "rule": "Ensure no overlap between 8B (Positive) and 8C (Negative) lists.", "on_fail": "HALT"}}, "seo_package": {"i": {"brand_voice_ref": "[REF to /shop_profile/brand_voice]"}, "rs": ["Bütünsel Sinerji (Başlık/Açıklama/Etiket tutarlılığı)", "Okunabilirlik ve Ton Analizi (Marka Sesi uyumu)", "CTA ve Güven Sinyalleri kontrolü"]}, "19": {"rs": ["Performans verilerinden genelleştirilmiş stratejik öğrenimler çıkar (Feedback Loop)."], "fl": {"post_action": "Write learnings to /_runtime/kb/strategic_learnings"}}}}}
}

changes_v17 = {
    "run": {"s": {"3p": {"n": "Otonom Persona ve Niş Tespiti (3p)", "description": "Görsel analiz (1a) ve Odak Anahtar Kelimeleri (3a) kullanarak Hedef Alıcı Personasını ve Estetik Nişi otonom olarak belirler.", "enabled": True, "i": {"visual_analysis": "[REF to Step 1a outputs]", "focus_keywords_and_intent": "[REF to Step 3a outputs]"}, "rs": ["Analyze visual cues (Step 1a) and keyword intent (Step 3a) to infer the primary Target Buyer Persona (e.g., Minimalist Bride, Vintage Collector, Gift Shopper).", "Analyze visuals and style keywords to define the core Aesthetic Niche (e.g., Art Deco, Boho, Modern, Minimalist).", "Use keyword intent data (3a) to refine the Persona's immediate need.", "Output a concise definition for both."], "o": {"strategy.target_persona": "string (inferred persona)", "strategy.aesthetic_niche": "string (inferred niche)"}, "requires": ["1a", "3a"], "c": {"must_confirm": False, "no_skip": True}}, "3b": {"requires": ["3p"]}, "10": {"requires": ["3p"]}, "11": {"requires": ["3p"]}, "12": {"requires": ["3p"]}, "14": {"requires": ["3p"]}, "seo_package": {"requires": ["3p"]}, "1a": {"rs": ["Analyze images for Thumbnail potential. Assign a 'CTR_Potential_Score' (1-100) based on clarity, composition, lighting, and relevance. Highlight the image ID with the highest score as 'best_candidate'."], "o": {"thumbnail_ctr_analysis": {"scores": [], "best_candidate_id": None}}}, "3a": {"rs": ["Revise Scoring Formula: Significantly increase the weight of 'Conversion Rate' (CR) and 'CTR' relative to 'Search Volume'. Prioritize high intent over high traffic.", "Segment the final focus keywords by 'Buyer Intent' (e.g., Research/Browsing, Gift-Specific Purchase, Self-Purchase)."], "o": {"keywords": {"focus_segmented": {"intent_groups": []}}}}, "5a": {"rs": ["Analyze top competitors' LQS Drivers: Identify their primary visual strategy (Lifestyle vs. Studio thumbnail), title structure emphasis (Feature vs. Benefit vs. Occasion frontloading), and price positioning relative to the market median."], "o": {"competitor_lqs_drivers_report": {"visual_strategy": None, "title_emphasis": None, "price_positioning": None}}}, "7": {"rs": ["Keyword Gap Analysis: Identify keywords with high CR/CTR present in the market data (Step 5a) but missing from our pool (Step 3a).", "Proactive Negative Generation: Based on Step 0 product info (e.g., if 'solid gold'), generate a list of irrelevant but high-traffic terms (e.g., 'plated', 'vermeil', 'filled')."], "o": {"keyword_gaps": [], "proactive_negatives_list": []}}, "8a": {"i": {"product_price_ref": "[REF to Step 0 price]", "conversion_rate_ref": "[REF to Step 3a CR data]"}, "rs": ["Calculate Estimated ROAS for each keyword group using the product price (Step 0) and Conversion Rate data (Step 3a). Propose a budget distribution weighted towards the highest Estimated ROAS groups."], "o": {"ads_budget_proposal": {"distribution": [], "roas_estimates": []}}}, "8C": {"i": {"proactive_negatives_ref": "[REF to Step 7 proactive_negatives_list]"}, "rs": ["Automatically merge the proactive_negatives_list from Step 7 into the final negative keyword set."]}, "10": {"i": {"focus_segmented_ref": "[REF to Step 3a keywords.focus_segmented]", "target_persona_ref": "[REF to Step 3p strategy.target_persona]"}, "rs": ["Dynamically structure the title based on the primary Buyer Intent (Step 3a) and Target Persona (Step 3p).", "ENFORCE Frontloading: The keyword with the highest Conversion Rate (CR) must appear within the first 40 characters."]}, "11": {"i": {"target_persona_ref": "[REF to Step 3p strategy.target_persona]"}, "rs": ["Implement Conversion Optimization Structure: Start with a benefit-driven hook, followed by a narrative tailored to the Target Persona (Step 3p), clear details, and strong trust signals (Shipping/Returns/Quality)."]}, "12": {"i": {"aesthetic_niche_ref": "[REF to Step 3p strategy.aesthetic_niche]"}, "rs": ["ENFORCE Multi-Word Rule: All 13 tags must contain at least 2 words (long-tail focus).", "Apply Strategic Distribution Model using inputs from 3p (Niche) and 3a (Intent). Example distribution: 4x Product Type, 3x Aesthetic Niche, 3x Buyer Intent/Occasion, 3x Material/Feature."]}, "14": {"i": {"thumbnail_ctr_ref": "[REF to 1a thumbnail_ctr_analysis]", "persona_niche_ref": "[REF to 3p outputs]"}, "rs": ["Calculate Simulated LQS (sLQS) score (1-100). Weighting Factors: Thumbnail CTR Potential (1a), Title Appeal/Relevance (10), Description Conversion Focus (11), and Persona/Niche Alignment (3p). Provide a breakdown."], "o": {"slqs_score": {"total": None, "breakdown": []}}}, "19": {"i": {"slqs_score_ref": "[REF to Step 14/seo_package slqs_score]"}, "rs": ["Diagnose performance bottlenecks: Identify if low performance is due to low CTR or low Conversion Rate.", "Compare actual performance metrics against the Simulated LQS (sLQS).", "Generate specific A/B test hypotheses targeting the identified bottleneck (e.g., If CTR is low, propose a Thumbnail test; if Conversion is low, propose a Description test)."], "o": {"performance_diagnosis": {}, "ab_test_hypotheses": []}}}}}
}


def main():
    print("--- Nihai, GitHub Entegreli Yükseltme Başlatılıyor (v16 & v17) ---")
    if not download_file(SOURCE_URL, LOCAL_SOURCE_FILE):
        return
    source_data = load_json_file(LOCAL_SOURCE_FILE)
    if source_data is None:
        return
    print("\n--- v16 Değişiklikleri Uygulanıyor ---")
    data_after_v16 = deep_update(OrderedDict(source_data), changes_v16)
    print("\n--- v17 Değişiklikleri Uygulanıyor ---")
    final_data = deep_update(data_after_v16, changes_v17)
    print("\n--- Yükseltme Tamamlandı. Sonuç dosyası kaydediliyor. ---")
    save_json_file(final_data, TARGET_FILE)
    print(f"\nGÖREV BAŞARIYLA TAMAMLANDI. {TARGET_FILE} oluşturuldu.")

if __name__ == "__main__":
    main()