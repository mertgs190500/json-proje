import logging

class TitleOptimizer:
    def __init__(self):
        self.MOBILE_CUTOFF = 40

    def execute(self, inputs, context):
        """
        Başlığı mobil öncelikli mimariye göre optimize eder.
        """
        logging.info("[TitleOptimizer] Başlık optimize ediliyor (Mobil Öncelikli).")
        
        primary = inputs.get("primary_keywords", [])
        secondary = inputs.get("secondary_keywords", [])
        intent = inputs.get("intent_keywords", [])

        if not primary:
            logging.error("Primary Keywords eksik.")
            return {"title": "Error"}

        title = " ".join(primary)
        if secondary:
            title += f" - {', '.join(secondary)}"
        if intent:
            title += f" | {', '.join(intent)}"
        title = title[:140]

        mobile_view = title[:self.MOBILE_CUTOFF]
        logging.info(f"[TitleOptimizer] Mobil Görünüm ({self.MOBILE_CUTOFF} karakter): {mobile_view}...")

        return {"title": title}