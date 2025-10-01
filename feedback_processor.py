import logging
import json

class FeedbackProcessor:
    def execute(self, inputs, context, db_manager=None):
        logging.info("[FeedbackProcessor] Geri besleme döngüsü başlatılıyor.")
        if not db_manager:
            logging.error("[FeedbackProcessor] DBManager sağlanmadı."); return {"status": "failed"}

        kb = db_manager.load_db("knowledge_base.json")
        if kb is None: kb = {"keyword_performance_weights": {}}
        weights = kb["keyword_performance_weights"]

        performance_data = inputs.get("performance_data", [])
        for item in performance_data:
            keyword, sales, traffic = item["keyword"], item["sales"], item["traffic"]
            if traffic > 0:
                ratio = sales / traffic
                if ratio > 0.05: weights[keyword] = round(weights.get(keyword, 1.0) * 1.1, 2)
                elif ratio < 0.01: weights[keyword] = round(weights.get(keyword, 1.0) * 0.9, 2)

        db_manager.save_db("knowledge_base.json", kb)
        logging.info("[FeedbackProcessor] Bilgi bankası güncellendi.")
        return {"status": "updated"}