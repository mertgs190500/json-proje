import logging
import random

class MabOptimizer:
    def __init__(self):
        self.EPSILON = 0.1 # Exploration rate (%10 Keşif)

    def _simulate_ctr(self, variation_id):
        # Gerçek senaryoda bu veri Etsy API'den gelir.
        # Simülasyon: V2'nin daha iyi performans gösterdiğini varsayalım.
        if variation_id == "V1": return 0.03
        if variation_id == "V2": return 0.05
        return 0.01

    def execute(self, inputs, context, db_manager=None):
        """
        MAB (Epsilon-Greedy) algoritmasını simüle eder.
        """
        variations = inputs.get("variations", [])
        logging.info(f"[MabOptimizer] Optimizasyon başlatılıyor. Varyasyon sayısı: {len(variations)}")

        stats = {v["id"]: {"impressions": 0, "clicks": 0, "ctr": 0.0} for v in variations}

        # 1000 gösterimlik trafik simülasyonu
        for i in range(1000):
            chosen_id = None
            # İlk turlarda veya Epsilon oranı tuttuğunda Keşif (Exploration) yap
            if i < 50 or random.random() < self.EPSILON:
                chosen_id = random.choice(list(stats.keys()))
            else:
                # Sömürü (Exploitation): En yüksek CTR'yi seç
                chosen_id = max(stats, key=lambda k: stats[k]["ctr"])

            # Performans simülasyonu
            stats[chosen_id]["impressions"] += 1
            if random.random() < self._simulate_ctr(chosen_id):
                stats[chosen_id]["clicks"] += 1

            # CTR güncelle
            data = stats[chosen_id]
            if data["impressions"] > 0:
                stats[chosen_id]["ctr"] = data["clicks"] / data["impressions"]

        # Sonuçları raporlama
        winner_id = max(stats, key=lambda k: stats[k]["ctr"])
        logging.info(f"[MabOptimizer] Optimizasyon tamamlandı. Kazanan: {winner_id}")

        # Geleneksel A/B testinden farklı olarak, MAB sayesinde kazanan varyasyon daha fazla trafik almıştır.
        return {"winner_id": winner_id, "performance_stats": stats}