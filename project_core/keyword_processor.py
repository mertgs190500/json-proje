import logging

class KeywordProcessor:

    def _collect(self, seed):
        logging.info("  [Alt Görev] Toplama...")
        return [seed, f"{seed} el yapımı", "fincan", "hediye"]

    def _filter(self, keywords):
        logging.info("  [Alt Görev] Filtreleme...")
        return [kw for kw in keywords if kw != "hediye"]

    def _merge(self, keywords, market_tags, visual_tags):
        logging.info("  [Alt Görev] Birleştirme (Pazar ve Görsel verileri ile)...")
        return list(set(keywords + market_tags + visual_tags))

    def _score_and_select(self, keywords, db_manager):
        logging.info("  [Alt Görev] Puanlama ve Seçim (Bilgi Bankası ile)...")
        if not db_manager:
            logging.warning("  DBManager sağlanmadı, puanlama atlanıyor.")
            return keywords

        kb = db_manager.load_db("knowledge_base.json")
        if not kb or "keyword_performance_weights" not in kb:
            logging.warning("  Bilgi bankası veya ağırlıklar bulunamadı, puanlama atlanıyor.")
            return keywords

        weights = kb["keyword_performance_weights"]

        sorted_keywords = sorted(keywords, key=lambda kw: weights.get(kw, 1.0), reverse=True)

        logging.info(f"  Puanlanmış ve sıralanmış anahtar kelimeler: {sorted_keywords}")
        return sorted_keywords

    def execute(self, inputs, context, db_manager=None):
        """
        Konsolide anahtar kelime hazırlama süreci.
        """
        logging.info("[KeywordProcessor] Konsolide hazırlık başlatılıyor.")

        # Girdiler uygulama.py tarafından çözümlenmiş olarak gelir
        seed = inputs.get("seed")
        market_tags = inputs.get("market_tags", [])
        visual_tags = inputs.get("visual_tags", [])

        # Adım içi veri akışı
        collected = self._collect(seed)
        filtered = self._filter(collected)
        merged = self._merge(filtered, market_tags, visual_tags)
        scored_and_selected = self._score_and_select(merged, db_manager)

        # Çıktı (StrategicKeywordData sözleşmesine uygun olmalı)
        output = {
            "coreKeywords": scored_and_selected[:5],
            "longTailKeywords": scored_and_selected[5:],
            "metrics": {"totalSearchVolume": len(scored_and_selected) * 100, "competitorDensity": 0.6}
        }
        logging.info("[KeywordProcessor] Hazırlık tamamlandı.")
        return output