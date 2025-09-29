import os
import json
import logging
import time
import google.generativeai as genai
import dotenv
import pandas as pd
from PIL import Image
import hashlib
import sys
from jsonpath_ng import jsonpath, parse

# --- FAZ 1: KURULUM VE YARDIMCI FONKSİYONLAR ---

# --- Maliyet Hesaplama Ayarları ---
MODEL_FIYATLARI_USD = {
    "gemini-2.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-2.5-flash": {"input": 0.35, "output": 1.05}
}
USD_TO_TRY_KURU = 43.0

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
            logging.error(f"'{filepath}' içinde beklenen SHA256 hash'i bulunamadı.")
            return None
        if calculated_hash == expected_hash:
            logging.info(f"'{filepath}' bütünlük kontrolünü geçti. Hash'ler eşleşiyor.")
            return config_data
        else:
            print("--- GÜVENLİK UYARISI: BÜTÜNLÜK ---")
            print(f"HATA: '{filepath}' dosyasının bütünlüğü doğrulanamadı.")
            print(f"Hesaplanan SHA256: {calculated_hash}")
            print(f"Beklenen SHA256:   {expected_hash}")
            logging.critical(f"BÜTÜNLÜK HATASI: '{filepath}'. Hesaplanan: {calculated_hash}, Beklenen: {expected_hash}")
            return None
    except Exception as e:
        print(f"HATA: Bütünlük kontrolü sırasında beklenmedik bir hata oluştu: {e}")
        logging.error(f"Bütünlük kontrolü hatası: {e}")
        return None

def kurulum_ve_yapilandirma():
    """Script başladığında gerekli tüm yapılandırmaları ve dosyaları yükler."""
    print("--- Faz 1: İnşaata Hazırlık Başlatıldı ---")
    dotenv.load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("API Anahtarı .env dosyasında bulunamadı.")
        print("HATA: .env dosyasında GEMINI_API_KEY bulunamadı.")
        return None, None
    try:
        genai.configure(api_key=api_key)
        logging.info("Gemini API anahtarı başarıyla yapılandırıldı.")
        print("-> Gemini API anahtarı yapılandırıldı.")
    except Exception as e:
        logging.error(f"Gemini API yapılandırılamadı: {e}")
        return None, None
    config_dosya_adi = "uretim_cekirdek_v15_revised.json"
    print(f"-> Üretim planı ('{config_dosya_adi}') yükleniyor ve doğrulanıyor...")
    config = verify_json_integrity(config_dosya_adi)
    if not config:
        print("-> Bütünlük kontrolü başarısız olduğu için işlem durduruldu.")
        sys.exit(1)
    print(f"-> Üretim planı başarıyla yüklendi ve doğrulandı.")
    logging.info(f"'{config_dosya_adi}' başarıyla yüklendi ve doğrulandı.")
    return config, api_key

def durum_yonetimi(config, adim_id=None, uretim_verileri=None, mod='yaz'):
    """
    Durum dosyasını (RUN_STATE.json) yönetir. Veri küçülme koruması içerir.
    """
    state_filepath = config.get("fs", {}).get("rt_p", {}).get("run_state_file", "RUN_STATE.json")

    if mod == 'oku':
        try:
            with open(state_filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            son_adim_id = state.get("last_completed_step_id")
            veriler = state.get("uretim_verileri", {})
            logging.info(f"Durum dosyası bulundu. Son tamamlanan adım: {son_adim_id}")
            print(f"-> Durum dosyası bulundu. Kaldığı yerden devam edilecek. Son adım: {son_adim_id}")
            for key, value in veriler.items():
                if isinstance(value, str) and '{"columns":' in value and ',"index":' in value:
                    try:
                        veriler[key] = pd.read_json(value, orient='split')
                    except Exception:
                        continue
            return son_adim_id, veriler
        except (FileNotFoundError, json.JSONDecodeError):
            logging.info("Durum dosyası bulunamadı. İş akışı en baştan başlatılacak.")
            print("-> Durum dosyası bulunamadı. İş akışı en baştan başlatılacak.")
            return None, {}

    elif mod == 'yaz':
        if uretim_verileri is None:
            return False

        guncel_uretim_verileri = uretim_verileri.copy()
        for key, value in guncel_uretim_verileri.items():
            if isinstance(value, pd.DataFrame):
                guncel_uretim_verileri[key] = value.to_json(orient='split')

        data_to_write = {"last_completed_step_id": adim_id, "uretim_verileri": guncel_uretim_verileri}
        new_state_bytes = json.dumps(data_to_write, ensure_ascii=False, indent=4).encode('utf-8')

        guard_rules = config.get("pl", {}).get("security", {}).get("size_shrink_guard", {})
        if guard_rules and os.path.exists(state_filepath):
            new_size = len(new_state_bytes)
            try:
                old_size = os.path.getsize(state_filepath)
                if old_size > 0:
                    size_diff = old_size - new_size
                    threshold_bytes = guard_rules.get("threshold_bytes", 4096)
                    threshold_ratio = guard_rules.get("threshold_percent", 0.005)
                    shrink_ratio_actual = size_diff / old_size if old_size > 0 else 0
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
            logging.info(f"Durum güncellendi. Son tamamlanan adım: {adim_id}")
            return True
        except Exception as e:
            print(f"HATA: Durum dosyası yazılırken beklenmedik bir hata oluştu: {e}")
            logging.error(f"Durum dosyası yazma hatası: {e}", exc_info=True)
            return False
    return None

def adim_icin_model_sec(adim_id):
    pro_model_adimlar = [
        '1a', '3a', '5a', '7', '8a', '9', '10', '11', '12', '19'
    ]
    if adim_id in pro_model_adimlar:
        return 'gemini-2.5-pro'
    else:
        return 'gemini-2.5-flash'

def csv_on_isleme_yap(dosya_yolu, kurallar):
    print(f"   -> Pandas ile yerel ön işleme başlatıldı: {dosya_yolu}")
    try:
        df = pd.read_csv(dosya_yolu, encoding='utf-8-sig', sep=None, engine='python')
        dedupe_sutun = kurallar.get("pre", {}).get("dedupe_on", [])
        if dedupe_sutun:
            df.drop_duplicates(subset=dedupe_sutun, inplace=True)
            print(f"   -> '{', '.join(dedupe_sutun)}' sütununa göre tekrarlar silindi.")
        print("   -> Yerel ön işleme tamamlandı.")
        return df
    except Exception as e:
        logging.error(f"Pandas ile CSV işlenirken hata: {e}")
        raise

def gorev_paketi_hazirla(adim_id, adim_detaylari, config, uretim_verileri):
    print(f"   -> Adım {adim_id} için tam bağlamlı görev paketi hazırlanıyor...")
    adim_kurallari = config.get("run", {}).get("s", {}).get(adim_id, {})
    prompt = f"Görevin, bir Etsy SEO uzmanı olarak, '{adim_detaylari}' (ID: {adim_id}) adımını gerçekleştirmektir.\n"
    prompt += f"Bu adımın ana kuralları (rs) şunlardır: {json.dumps(adim_kurallari.get('rs', {}))}\n"
    gerekli_girdiler = adim_kurallari.get('i', [])
    if gerekli_girdiler:
        prompt += "\nİşlemde kullanılacak GEREKLİ GİRDİLER VE BAĞLAM (i) aşağıdadır:\n"
        girdi_kaynak_haritasi = {
            "keywords.focus": "adim_3a_sonuc", "seo.keywords.supporting": "adim_9_sonuc",
            "title.final": "adim_10_sonuc", "description.final": "adim_11_sonuc",
            "tags.final": "adim_12_sonuc", "draft.title": "adim_3b_sonuc",
            "popular.products.top": "adim_5a_sonuc", "competitors.selected": "adim_5b_sonuc",
            "market.snapshot": "adim_7_sonuc", "ads.plan": "adim_8a_sonuc",
            "ads.keywords.final": "adim_8C_sonuc", "benzer_kelimeler_df": "benzer_kelimeler_df",
            "populer_urunler_df": "populer_urunler_df", "rakip_urunler_df": "rakip_urunler_df",
        }
        for girdi_anahtari_json in gerekli_girdiler:
            veri, veri_anahtari_uretim = None, None
            for kaynak_key, uretim_key in girdi_kaynak_haritasi.items():
                if kaynak_key in girdi_anahtari_json:
                    veri_anahtari_uretim = uretim_key
                    break
            if "product.info" in girdi_anahtari_json or "shop.profile" in girdi_anahtari_json:
                veri = config.get('product_record', {})
            if veri_anahtari_uretim:
                veri = uretim_verileri.get(veri_anahtari_uretim)
            if veri is not None:
                if isinstance(veri, pd.DataFrame):
                    prompt += f"- {girdi_anahtari_json}: (DataFrame mevcut, {len(veri)} satır içeriyor, ilk 2 satır: {veri.head(2).to_string()})\n"
                else:
                    prompt += f"- {girdi_anahtari_json}: {str(veri)}\n"
            else:
                prompt += f"- UYARI: Gerekli girdi '{girdi_anahtari_json}' üretim verileri içinde bulunamadı.\n"
    beklenen_ciktilar = adim_kurallari.get('o', None)
    if beklenen_ciktilar:
        prompt += f"\nBEKLENEN ÇIKTI FORMATI (o):\n"
        prompt += f"Lütfen cevabını bu yapıya uygun olarak formatla: {json.dumps(beklenen_ciktilar)}\n"
    kisitlar = adim_kurallari.get('g', None)
    dogrulayicilar = adim_kurallari.get('vlds', None)
    if kisitlar or dogrulayicilar:
        prompt += "\nKISITLAR ve KONTROLLER (g/vlds):\n"
        prompt += "Üreteceğin çıktı, aşağıdaki kısıtlar ve doğrulama kurallarına göre sistem tarafından kontrol edilecektir. Lütfen bu kurallara azami dikkat göster:\n"
        if kisitlar:
            prompt += f"- Kısıtlar: {json.dumps(kisitlar)}\n"
        if dogrulayicilar:
            prompt += f"- Doğrulayıcılar: {json.dumps(dogrulayicilar)}\n"
    print(f"   -> Görev paketi hazırlandı. Boyut: {len(prompt)} karakter.")
    return prompt

# --- FAZ 2: İŞ AKIŞI MOTORU ---

def on_kosullari_kontrol_et(adim_id, config, uretim_verileri):
    """
    Bir adımın başlaması için gereken ön koşulları (precon) kontrol eder.
    JPath ifadelerini kullanarak 'uretim_verileri' (RUN_STATE) içinde arama yapar.
    """
    adim_kurallari = config.get("run", {}).get("s", {}).get(adim_id, {})
    on_kosullar = adim_kurallari.get("precon")
    if not on_kosullar:
        logging.debug(f"Adım '{adim_id}' için ön koşul bulunmuyor, devam ediliyor.")
        return True
    logging.debug(f"Adım '{adim_id}' için ön koşullar kontrol ediliyor: {on_kosullar}")
    if "all_must_be_true" in on_kosullar:
        for kural in on_kosullar["all_must_be_true"]:
            jpath_ifadesi = kural.get("JPath")
            beklenen_ifade = kural.get("expr")
            if not jpath_ifadesi or not beklenen_ifade:
                logging.warning(f"Adım '{adim_id}' için geçersiz ön koşul kuralı: {kural}")
                continue
            try:
                jsonpath_expression = parse(jpath_ifadesi)
                bulunanlar = jsonpath_expression.find(uretim_verileri)
                if beklenen_ifade == "exists":
                    if not bulunanlar:
                        logging.warning(f"Ön koşul BAŞARISIZ ('{jpath_ifadesi}' -> exists): Adım '{adim_id}' için gerekli veri bulunamadı.")
                        return False
                elif beklenen_ifade == "not exists":
                    if bulunanlar:
                        logging.warning(f"Ön koşul BAŞARISIZ ('{jpath_ifadesi}' -> not exists): Adım '{adim_id}' için beklenmeyen veri bulundu.")
                        return False
                else:
                     logging.warning(f"Adım '{adim_id}' için bilinmeyen ön koşul ifadesi: '{beklenen_ifade}'")
            except Exception as e:
                logging.error(f"Adım '{adim_id}' ön koşulunu işlerken JPath hatası: {e}")
                return False
    logging.info(f"Adım '{adim_id}' tüm ön koşulları başarıyla geçti.")
    return True

def ciktiyi_dogrula(adim_id, model_ciktisi, config):
    """
    Modelin ürettiği çıktının, JSON'da tanımlanan kısıtlar (g) ve
    doğrulayıcılara (vlds) uyup uymadığını kontrol eder.
    """
    adim_kurallari = config.get("run", {}).get("s", {}).get(adim_id, {})
    kisitlar = adim_kurallari.get("g", {})
    dogrulayicilar = adim_kurallari.get("vlds", {})
    if not kisitlar and not dogrulayicilar:
        return True
    if adim_id == '12':
        try:
            cikti_listesi = json.loads(model_ciktisi.replace("'", "\""))
            if isinstance(cikti_listesi, list) and len(cikti_listesi) != 13:
                logging.error(f"Adım {adim_id} doğrulama BAŞARISIZ: Beklenen 13 etiket yerine {len(cikti_listesi)} adet üretildi.")
                return False
        except Exception:
            logging.error(f"Adım {adim_id} doğrulama BAŞARISIZ: Model çıktısı beklenen formatta değil.")
            return False
    return True

def is_akisi_motoru(config):
    """JSON dosyasındaki adımları sırayla çalıştıran ana motor."""
    print("\n--- Faz 2: Üretim Başlatıldı ---")
    adim_listesi = config.get("run", {}).get("steps_list_snapshot", [])
    if not adim_listesi:
        logging.error("JSON'da 'run.steps_list_snapshot' bulunamadı.")
        return
    son_tamamlanan_adim_id, uretim_verileri = durum_yonetimi(config, mod='oku')
    baslangic_index = 0
    if son_tamamlanan_adim_id:
        try:
            adim_idler = [s.get('id') for s in adim_listesi]
            baslangic_index = adim_idler.index(son_tamamlanan_adim_id) + 1
        except (ValueError, AttributeError):
            print(f"UYARI: Kayıtlı adım '{son_tamamlanan_adim_id}' güncel akışta bulunamadı. Baştan başlanıyor.")
            uretim_verileri = {}
    maliyet_raporu = uretim_verileri.get("maliyet_raporu", {
        "toplam_girdi_token": 0, "toplam_cikti_token": 0,
        "toplam_maliyet_tl": 0.0, "adimlar": {}
    })
    uretim_klasoru = "uretim/1"
    print(f"UYARI: Script, '{uretim_klasoru}' klasöründeki dosyaları izleyecektir.")
    if not os.path.exists(uretim_klasoru):
        os.makedirs(uretim_klasoru)
    i = baslangic_index
    while i < len(adim_listesi):
        adim_objesi = adim_listesi[i]
        adim_id = adim_objesi.get("id")
        adim_detaylari = adim_objesi.get("n", adim_id)
        print(f"\n▶ Adım {i+1}/{len(adim_listesi)} (ID: {adim_id}) başlatılıyor: {adim_detaylari}...")
        logging.info(f"Adım {adim_id} başlatılıyor: {adim_detaylari}")
        if not on_kosullari_kontrol_et(adim_id, config, uretim_verileri):
            print(f"   -> UYARI: Adım {adim_id} için ön koşullar sağlanamadı. Bu adım atlanıyor.")
            logging.warning(f"Adım {adim_id} ön koşullar sağlanamadığı için atlandı.")
            i += 1
            continue
        try:
            dosya_bekleme_haritasi = {
                "1": {"tur": "gorsel", "beklenen_dosya_sayisi": 5},
                "3": {"tur": "csv", "dosya_adi": "similar_keywords.csv", "kural_anahtari": "similar_keywords", "veri_anahtari": "benzer_kelimeler_df"},
                "5": {"tur": "csv", "dosya_adi": "top_listings.csv", "kural_anahtari": "popular_listings", "veri_anahtari": "populer_urunler_df"},
                "6a": {"tur": "csv", "dosya_adi": "competitor_listings.csv", "kural_anahtari": "competitor_csv", "veri_anahtari": "rakip_urunler_df"},
            }
            if adim_id == "16":
                print(f"   -> ▷ KULLANICI EYLEMİ GEREKLİ: Üretim tamamlandı.")
                while True:
                    kullanici_girdisi = input("   -> Lütfen kayıt türünü seçin (publish / draft / preview): ").lower().strip()
                    if kullanici_girdisi in ["publish", "draft", "preview"]:
                        uretim_verileri['kayit_turu'] = kullanici_girdisi
                        print(f"   -> Kayıt türü '{kullanici_girdisi}' olarak ayarlandı.")
                        break
                    else:
                        print("   -> Geçersiz komut. Lütfen 'publish', 'draft' veya 'preview' yazın.")
            elif adim_id in dosya_bekleme_haritasi:
                adim_bilgisi = dosya_bekleme_haritasi[adim_id]
                while True:
                    print(f"   -> ▷ KULLANICI EYLEMİ GEREKLİ: Lütfen '{adim_id}' adımı için gerekli dosyaları '{uretim_klasoru}' klasörüne kopyalayın.")
                    if adim_bilgisi['tur'] == 'csv':
                        beklenen_dosya = os.path.join(uretim_klasoru, adim_bilgisi['dosya_adi'])
                        if os.path.exists(beklenen_dosya):
                            print(f"   -> '{adim_bilgisi['dosya_adi']}' bulundu. İşleniyor...")
                            csv_kurallari = config.get("csv", {}).get(adim_bilgisi['kural_anahtari'], {})
                            temiz_veri_df = csv_on_isleme_yap(beklenen_dosya, csv_kurallari)
                            uretim_verileri[adim_bilgisi['veri_anahtari']] = temiz_veri_df
                            break
                    elif adim_bilgisi['tur'] == 'gorsel':
                        mevcut_gorseller = [f for f in os.listdir(uretim_klasoru) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                        print(f"   -> Beklenen görsel sayısı: {adim_bilgisi['beklenen_dosya_sayisi']}, Mevcut görsel sayısı: {len(mevcut_gorseller)}")
                        if len(mevcut_gorseller) >= adim_bilgisi['beklenen_dosya_sayisi']:
                            print(f"   -> Gerekli sayıda görsel bulundu. Devam ediliyor...")
                            uretim_verileri['gorsel_listesi'] = mevcut_gorseller
                            break
                    time.sleep(15)
            else:
                secilen_model_adi = adim_icin_model_sec(adim_id)
                print(f"   -> Bu adım için '{secilen_model_adi}' modeli kullanılacak.")
                prompt = gorev_paketi_hazirla(adim_id, adim_detaylari, config, uretim_verileri)
                model = genai.GenerativeModel(secilen_model_adi)
                print("   -> Gemini'ye istek gönderiliyor...")
                yanit = model.generate_content(prompt)
                if hasattr(yanit, 'usage_metadata') and yanit.usage_metadata:
                    girdi_token = yanit.usage_metadata.prompt_token_count
                    cikti_token = yanit.usage_metadata.candidates_token_count
                    fiyatlar = MODEL_FIYATLARI_USD.get(secilen_model_adi, {"input": 0, "output": 0})
                    maliyet_usd = ((girdi_token / 1000000) * fiyatlar['input']) + ((cikti_token / 1000000) * fiyatlar['output'])
                    maliyet_tl = maliyet_usd * USD_TO_TRY_KURU
                    maliyet_raporu["adimlar"][adim_id] = {
                        "girdi_token": girdi_token, "cikti_token": cikti_token, "maliyet_tl": round(maliyet_tl, 4)
                    }
                    maliyet_raporu["toplam_girdi_token"] += girdi_token
                    maliyet_raporu["toplam_cikti_token"] += cikti_token
                    maliyet_raporu["toplam_maliyet_tl"] += maliyet_tl
                    uretim_verileri['maliyet_raporu'] = maliyet_raporu
                    print(f"   -> Bu adımın token kullanımı: Girdi={girdi_token}, Çıktı={cikti_token}. Tahmini Maliyet: {round(maliyet_tl, 4)} TL")
                print("\n   --- Gemini'nin Yanıtı ---")
                print(yanit.text)
                print("   -------------------------\n")
                if not ciktiyi_dogrula(adim_id, yanit.text, config):
                    print(f"   -> HATA: Adım {adim_id} çıktısı kalite kontrolünden geçemedi.")
                    adim_kurallari = config.get("run", {}).get("s", {}).get(adim_id, {})
                    hata_yonetimi = adim_kurallari.get("on_error", {})
                    if hata_yonetimi.get("pol") == "fail-soft":
                        print("   -> 'fail-soft' kuralı gereği bir sonraki adımla devam ediliyor.")
                        logging.warning(f"Adım {adim_id} çıktı doğrulamasını geçemedi ancak 'fail-soft' ile devam ediyor.")
                        i += 1
                        continue
                    elif "fallback_next" in hata_yonetimi:
                        fallback_adim_id = hata_yonetimi["fallback_next"]
                        print(f"   -> 'fallback_next' kuralı gereği '{fallback_adim_id}' adımına atlanıyor.")
                        logging.warning(f"Adım {adim_id} çıktı doğrulamasını geçemedi. Fallback -> {fallback_adim_id}")
                        try:
                            adim_idler = [s.get('id') for s in adim_listesi]
                            i = adim_idler.index(fallback_adim_id)
                            continue
                        except ValueError:
                            print(f"   -> HATA: Fallback adımı '{fallback_adim_id}' akışta bulunamadı. İşlem durduruluyor.")
                            break
                    else:
                        print("   -> İş akışı durduruluyor.")
                        break
                uretim_verileri[f'adim_{adim_id}_sonuc'] = yanit.text
                print("   -> Yanıt saklandı.")
            print(f"✔ Adım {adim_id} başarıyla tamamlandı.")
            durum_yonetimi(config, adim_id, uretim_verileri, mod='yaz')
            i += 1
        except Exception as e:
            adim_kurallari = config.get("run", {}).get("s", {}).get(adim_id, {})
            hata_yonetimi = adim_kurallari.get("on_error", {})
            if hata_yonetimi.get("pol") == "fail-soft":
                print(f"   -> UYARI: Adım {adim_id} sırasında bir hata oluştu ('{e}'), ancak 'fail-soft' kuralı gereği bir sonraki adımla devam ediliyor.")
                logging.warning(f"Adım {adim_id} 'fail-soft' ile hatayı geçti: {e}")
                i += 1
                continue
            elif "fallback_next" in hata_yonetimi:
                fallback_adim_id = hata_yonetimi["fallback_next"]
                print(f"   -> HATA: Adım {adim_id} çalıştırılırken bir hata oluştu ('{e}'). 'fallback_next' kuralı gereği '{fallback_adim_id}' adımına atlanıyor.")
                logging.warning(f"Adım {adim_id} hatası. Fallback -> {fallback_adim_id}. Hata: {e}")
                try:
                    adim_idler = [s.get('id') for s in adim_listesi]
                    i = adim_idler.index(fallback_adim_id)
                    continue
                except ValueError:
                    print(f"   -> HATA: Fallback adımı '{fallback_adim_id}' akışta bulunamadı. İşlem durduruluyor.")
                    break
            else:
                logging.error(f"Adım {adim_id} sırasında kritik bir hata oluştu: {e}")
                print(f"\n--- HATA ---")
                print(f"Adım {adim_id} çalıştırılırken bir hata oluştu: {e}")
                if config.get("r", {}).get("stop_err", True):
                    print("Kural gereği işlem durduruluyor.")
                    break
    print("\n--- İş Akışı Tamamlandı ---")
    if maliyet_raporu["adimlar"]:
        print("\n--- ÜRETİM MALİYET RAPORU ---")
        for adim, maliyet in maliyet_raporu.get("adimlar", {}).items():
            adim_label = config.get('run', {}).get('labels', {}).get(adim, adim)
            print(f"Adım {adim} ({adim_label}):")
            print(f"  - Girdi: {maliyet.get('girdi_token', 0)} token, Çıktı: {maliyet.get('cikti_token', 0)} token")
            print(f"  - Tahmini Maliyet: {maliyet.get('maliyet_tl', 0.0)} TL")
        print("\n---------------------------------")
        print("TOPLAM KULLANIM:")
        print(f"  - Toplam Girdi: {maliyet_raporu.get('toplam_girdi_token', 0)} token")
        print(f"  - Toplam Çıktı: {maliyet_raporu.get('toplam_cikti_token', 0)} token")
        print(f"  - TAHMINI TOPLAM MALIYET: {round(maliyet_raporu.get('toplam_maliyet_tl', 0.0), 2)} TL")
        print("---------------------------------")

# --- ANA ÇALIŞTIRMA BLOĞU ---
if __name__ == "__main__":
    logging.basicConfig(
        filename='uretim_gunlugu.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )
    config, api_key = kurulum_ve_yapilandirma()
    if config and api_key:
        is_akisi_motoru(config)
    else:
        print("Kurulum veya yapılandırma başarısız oldu. Script sonlandırılıyor.")