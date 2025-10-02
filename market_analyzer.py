import logging
import pandas as pd
from collections import Counter

class MarketAnalyzer:
    def _clean_price(self, price_series):
        """Fiyat/Gelir sütunlarını temizler ($ ve , kaldırır)."""
        return pd.to_numeric(price_series.astype(str).str.replace(r'[$,]', '', regex=True), errors='coerce')

    def execute(self, inputs, context):
        """
        Verilen CSV dosyasını okur, temizler ve pazar analizi yapar.
        """
        csv_path = inputs.get("csv_path")
        if not csv_path:
            logging.error("[MarketAnalyzer] CSV dosya yolu belirtilmemiş.")
            return None

        logging.info(f"[MarketAnalyzer] Pazar analizi başlatılıyor: {csv_path}")

        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            logging.error(f"[MarketAnalyzer] CSV dosyası bulunamadı: {csv_path}")
            return None
            
        # --- Veri Temizleme ---
        # Fiyat ve Gelir sütunlarını temizle
        price_col = 'Price'
        if price_col in df.columns:
            df[price_col] = self._clean_price(df[price_col])
        
        # --- Analiz ---
        # 1. Fiyat Aralığı Analizi
        avg_price = df[price_col].mean() if price_col in df.columns else 0.0

        # 2. En Popüler Etiketler Analizi
        all_tags = []
        if 'Tags' in df.columns:
            # Eksik değerleri boş string ile doldur ve etiketleri ayır
            tag_lists = df['Tags'].dropna().str.split(',')
            # Tüm etiketleri tek bir listeye topla ve boşlukları temizle
            all_tags = [tag.strip() for sublist in tag_lists for tag in sublist]

        # En sık kullanılan 10 etiketi bul
        top_10_tags = [tag for tag, count in Counter(all_tags).most_common(10)]

        # --- Çıktıyı Veri Sözleşmesine Uygun Hale Getirme ---
        output = {
            "topCompetitorTags": top_10_tags,
            "priceRange": {
                "avg": round(avg_price, 2)
            }
        }
        
        logging.info("[MarketAnalyzer] Analiz tamamlandı.")
        return output