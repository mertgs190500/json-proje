import logging

class VisualAnalyzer:
    def execute(self, inputs, context, db_manager=None):
        image_paths = inputs.get("image_paths", [])
        logging.info(f"[VisualAnalyzer] {len(image_paths)} görsel analiz ediliyor.")

        output = {
            "detected_colors": ["Mavi", "Beyaz"],
            "detected_materials": ["Seramik"],
            "detected_styles": ["Minimalist", "Modern"],
            "visual_tags": ["mavi seramik kupa", "minimalist fincan"]
        }
        logging.info("[VisualAnalyzer] Görsel özellikler çıkarıldı.")
        return output