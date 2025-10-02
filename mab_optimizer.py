import logging
import random

class MabOptimizer:
    def __init__(self):
        self.EPSILON = 0.1 # %10 Keşif oranı

    def _simulate_ctr(self, variation_id):
        # Gerçek senaryoda bu veri Etsy API'den gelir. V2'nin daha iyi olduğunu varsayalım.
        if variation_id == "V1": return 0.03
        if variation_id == "V2": return 0.05
        return 0.01

    def execute(self, inputs, context):
        """
        MAB (Epsilon-Greedy) algoritmasını simüle eder.
        """
        variations = inputs.get("variations", [])
        logging.info(f"[MabOptimizer] Optimizasyon başlatılıyor. Varyasyon sayısı: {len(variations)}")
        stats = {v["id"]: {"impressions": 0, "clicks": 0, "ctr": 0.0} for v in variations}
        
        for i in range(1000): # 1000 gösterimlik trafik simülasyonu
            chosen_id = None
            if i < 50 or random.random() < self.EPSILON:
                chosen_id = random.choice(list(stats.keys()))
            else:
                chosen_id = max(stats, key=lambda k: stats[k]["ctr"])

            stats[chosen_id]["impressions"] += 1
            if random.random() < self._simulate_ctr(chosen_id):
                stats[chosen_id]["clicks"] += 1
            
            if stats[chosen_id]["impressions"] > 0:
                stats[chosen_id]["ctr"] = stats[chosen_id]["clicks"] / stats[chosen_id]["impressions"]

        winner_id = max(stats, key=lambda k: stats[k]["ctr"])
        logging.info(f"[MabOptimizer] Optimizasyon tamamlandı. Kazanan: {winner_id}")
        
        return {"winner_id": winner_id, "performance_stats": stats}