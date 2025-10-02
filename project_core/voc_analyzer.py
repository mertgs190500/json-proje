import logging

class VocAnalyzer:
    def execute(self, inputs, context, db_manager=None):
        """
        Müşteri yorumlarını analiz eder (NLP Simülasyonu).
        """
        reviews = inputs.get("reviews", [])
        logging.info(f"[VocAnalyzer] {len(reviews)} yorum analiz ediliyor.")

        # Basit anahtar kelime tabanlı duygu analizi simülasyonu
        positive = set()
        negative = set()
        phrases = []

        for review in reviews:
            text = review.lower()
            if "hızlı kargo" in text or "mükemmel kalite" in text:
                positive.add("Kalite ve Hız")
                phrases.append("Hızlı kargo garantisiyle sunulan üstün kalite.")
            if "beklediğimden küçük" in text or "rengi soluk" in text:
                negative.add("Boyut/Renk Beklentisi")
                phrases.append("Canlı renkler ve net boyut bilgisi için fotoğrafları inceleyin.")

        output = {
            "positiveThemes": list(positive),
            "negativeThemes": list(negative),
            "benefitDrivenPhrases": list(set(phrases))
        }
        logging.info("[VocAnalyzer] Analiz tamamlandı.")
        return output