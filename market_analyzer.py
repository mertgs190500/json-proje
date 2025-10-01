import logging

# Not: Sınıf adı dosya adıyla uyumlu olmalı (market_analyzer -> MarketAnalyzer)
class MarketAnalyzer:
    def execute(self, inputs, context):
        """
        Pazar verilerini analiz eder (Simülasyon).
        Gerçek senaryoda eRank veya benzeri API'lere bağlanır.
        """
        niche = inputs.get("niche", "Bilinmiyor")
        logging.info(f"[MarketAnalyzer] Niş analiz ediliyor: {niche}")

        # Simüle edilmiş veri
        output = {
            "topCompetitorTags": ["minimalist takı", "gümüş kolye", "doğum günü hediyesi"],
            "priceRange": {"min": 25.00, "max": 75.00, "avg": 48.50}
        }
        logging.info("[MarketAnalyzer] Analiz tamamlandı.")
        return output