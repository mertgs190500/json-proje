import logging

class TitleOptimizer:
    def __init__(self):
        self.MOBILE_CUTOFF = 40 # Rapor 2.3.2'ye göre kritik mobil görünüm karakter sayısı

    def execute(self, inputs, context):
        """
        Başlığı mobil öncelikli mimariye göre optimize eder.
        """
        logging.info("[TitleOptimizer] Başlık optimize ediliyor (Mobil Öncelikli).")

        # Girdileri al (Gerçek senaryoda bunlar context'ten gelecektir)
        primary = inputs.get("primary_keywords", [])
        secondary = inputs.get("secondary_keywords", [])
        intent = inputs.get("intent_keywords", [])

        if not primary:
            logging.error("Primary Keywords eksik.")
            return {"title": "Error"}

        # 1. Çekirdek Tanım (En önemli kısım, mobil görünümde olmalı)
        title = " ".join(primary)

        # 2. İkincil Bilgiler (Özellikler/Materyal)
        if secondary:
            title += f" - {', '.join(secondary)}"

        # 3. Niyet/Amaç (Sonda yer alır - Rapor 2.3.2)
        if intent:
            title += f" | {', '.join(intent)}"

        # Uzunluk kontrolü
        title = title[:140]

        # Mobil etki analizi (Loglama)
        mobile_view = title[:self.MOBILE_CUTOFF]
        logging.info(f"[TitleOptimizer] Mobil Görünüm ({self.MOBILE_CUTOFF} karakter): {mobile_view}...")

        return {"title": title}