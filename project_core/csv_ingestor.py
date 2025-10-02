import logging
import pandas as pd

class CsvIngestor:
    def execute(self, inputs, context, db_manager=None):
        file_path = inputs.get("file_path")
        profile = inputs.get("resolved_profile", {})

        if not profile:
            logging.error("[CsvIngestor] Profil bilgisi alınamadı.")
            return {"topCompetitorTags": [], "priceRange": {"avg": 0}}

        logging.info(f"[CsvIngestor] Dosya işleniyor: {file_path} using profile")

        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            logging.error(f"[CsvIngestor] CSV dosyası bulunamadı: {file_path}")
            return {"topCompetitorTags": [], "priceRange": {"avg": 0}}

        # Apply deduplication from the profile
        dedupe_cols = profile.get("dedupe_on")
        if dedupe_cols:
            initial_rows = len(df)
            df.drop_duplicates(subset=dedupe_cols, inplace=True)
            logging.info(f"  Deduplikasyon uygulandı ({initial_rows - len(df)} satır kaldırıldı).")

        # Simulate extracting tags from titles
        tags = set()
        if 'Title' in df.columns:
            for title in df['Title'].dropna():
                tags.update(title.lower().split())

        # Calculate price range
        price_range = {"min": 0, "max": 0, "avg": 0}
        if 'Price' in df.columns and not df['Price'].empty:
            price_series = pd.to_numeric(df['Price'], errors='coerce').dropna()
            if not price_series.empty:
                price_range["min"] = price_series.min()
                price_range["max"] = price_series.max()
                price_range["avg"] = price_series.mean()

        output = {
            "topCompetitorTags": list(tags),
            "priceRange": price_range
        }

        logging.info("[CsvIngestor] CSV analizi tamamlandı.")
        return output