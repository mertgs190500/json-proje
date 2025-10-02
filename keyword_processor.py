import logging

class KeywordProcessor:
    
    def _collect(self, seed):
        logging.info("  [Alt Görev] Toplama...")
        return [seed, f"{seed} el yapımı", "fincan", "hediye"]

    def _filter(self, keywords):
        logging.info("  [Alt Görev] Filtreleme...")
        return [kw for kw in keywords if kw != "hediye"]

    def _merge(self, keywords, market_tags):
        logging.info("  [Alt Görev] Birleştirme (Pazar verileri ile)...")
        return list(set(keywords + market_tags))

    def execute(self, inputs, context):
        """
        Konsolide anahtar kelime hazırlama süreci.
        """
        logging.info("[KeywordProcessor] Konsolide hazırlık başlatılıyor.")
        
        seed = inputs.get("seed")
        market_tags = inputs.get("market_tags", [])

        collected = self._collect(seed)
        filtered = self._filter(collected)
        merged = self._merge(filtered, market_tags)

        output = {
            "coreKeywords": merged[:5],
            "longTailKeywords": merged[5:],
            "metrics": {"totalSearchVolume": len(merged) * 100, "competitorDensity": 0.6}
        }
        logging.info("[KeywordProcessor] Hazırlık tamamlandı.")
        return output