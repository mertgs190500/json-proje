import logging
import random

class MabOptimizer:
    def __init__(self):
        self.EPSILON = 0.1 # 10% exploration rate

    def _simulate_ctr(self, variation_id):
        """Simulates the Click-Through Rate for a given variation."""
        # In a real scenario, this data would come from an external analytics service.
        # For this simulation, we assume V2 consistently performs better.
        if variation_id == "V1": return 0.03 # 3% CTR for the control
        if variation_id == "V2": return 0.05 # 5% CTR for the challenger
        return 0.01 # Default low CTR for other variations

    def execute(self, inputs, context, db_manager=None):
        """
        Simulates a Multi-Armed Bandit (MAB) optimization using Epsilon-Greedy.
        """
        variations = inputs.get("variations", [])
        if not variations:
            logging.warning("[MabOptimizer] No variations provided for optimization.")
            return {"winner_id": None, "performance_stats": {}}

        logging.info(f"[MabOptimizer] Optimization started. Number of variations: {len(variations)}")

        stats = {v["id"]: {"impressions": 0, "clicks": 0, "ctr": 0.0} for v in variations}

        # Simulate a run of 1000 impressions
        for i in range(1000):
            chosen_id = None
            # Exploration: In the first few rounds or based on the epsilon chance, choose randomly.
            if i < 50 or random.random() < self.EPSILON:
                chosen_id = random.choice([v["id"] for v in variations])
            else:
                # Exploitation: Choose the arm with the highest known CTR.
                chosen_id = max(stats, key=lambda k: stats[k]["ctr"])

            # Simulate performance and update stats
            stats[chosen_id]["impressions"] += 1
            if random.random() < self._simulate_ctr(chosen_id):
                stats[chosen_id]["clicks"] += 1

            # Recalculate CTR for the chosen arm
            data = stats[chosen_id]
            if data["impressions"] > 0:
                stats[chosen_id]["ctr"] = data["clicks"] / data["impressions"]

        # Determine the final winner based on the simulation
        winner_id = max(stats, key=lambda k: stats[k]["ctr"])
        logging.info(f"[MabOptimizer] Optimization complete. Winner: {winner_id}")

        # Unlike a traditional A/B test, MAB allocates more traffic to the better-performing variation during the test.
        return {"winner_id": winner_id, "performance_stats": stats}