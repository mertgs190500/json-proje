import logging

class TitleOptimizer:
    def __init__(self):
        self.MOBILE_CUTOFF = 40 # Critical character count for mobile view as per Report 2.3.2

    def execute(self, inputs, context, db_manager=None):
        """
        Optimizes the title based on a mobile-first architecture.
        """
        logging.info("[TitleOptimizer] Optimizing title (Mobile-First).")

        primary = inputs.get("primary_keywords", [])
        secondary = inputs.get("secondary_keywords", [])
        intent = inputs.get("intent_keywords", [])

        if not primary:
            logging.error("Primary Keywords are missing.")
            return {"title": "Error: Missing Primary Keywords"}

        # 1. Core Definition (Most important part, must be in mobile view)
        title = " ".join(primary)

        # 2. Secondary Info (Features/Material)
        if secondary:
            title += f" - {', '.join(secondary)}"

        # 3. Intent/Purpose (Positioned at the end - Report 2.3.2)
        if intent:
            title += f" | {', '.join(intent)}"

        # Enforce length constraint
        title = title[:140]

        # Log a mobile impact analysis
        mobile_view = title[:self.MOBILE_CUTOFF]
        logging.info(f"[TitleOptimizer] Mobile View ({self.MOBILE_CUTOFF} chars): {mobile_view}...")

        return {"title": title}