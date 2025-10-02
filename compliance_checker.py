import logging

class ComplianceChecker:
    """
    Checks all generated text and media content for compliance with internal
    and external policies (e.g., Etsy, Google).
    """

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution method. It validates the listing data against a set of rules.

        Args:
            inputs (dict): A dictionary containing the listing data to be checked,
                           e.g., {'title': '...', 'description': '...', 'tags': [...]}.

        Returns:
            dict: A status report, e.g., {"status": "PASS", "issues": []}.
        """
        logging.info("[ComplianceChecker] Starting compliance check.")

        listing_data = inputs.get("listing_data", {})
        policy_rules = inputs.get("policy_rules", {}) # Rules loaded from config

        issues = []

        # --- Rule Simulation ---
        # In a real scenario, these rules would be more extensive and loaded from finalv1.json.
        forbidden_terms = policy_rules.get("forbidden_terms", ["restricted", "prohibited_brand"])
        required_disclaimers = policy_rules.get("required_disclaimers", ["Handmade item"])

        # Combine all text content for easier checking
        full_text = (
            listing_data.get("title", "") + " " +
            listing_data.get("description", "") + " " +
            " ".join(listing_data.get("tags", []))
        ).lower()

        # 1. Check for forbidden terms
        for term in forbidden_terms:
            if term.lower() in full_text:
                issues.append({
                    "code": "FORBIDDEN_TERM",
                    "message": f"Detected forbidden term: '{term}'.",
                    "severity": "FAIL"
                })

        # 2. Check for required disclaimers
        description_text = listing_data.get("description", "").lower()
        for disclaimer in required_disclaimers:
            if disclaimer.lower() not in description_text:
                issues.append({
                    "code": "MISSING_DISCLAIMER",
                    "message": f"Missing required disclaimer: '{disclaimer}'.",
                    "severity": "WARN"
                })

        # --- Determine Final Status ---
        final_status = "PASS"
        if any(issue['severity'] == 'FAIL' for issue in issues):
            final_status = "FAIL"
        elif issues: # If there are only warnings
            final_status = "WARN"

        logging.info(f"[ComplianceChecker] Check complete. Status: {final_status}, Issues found: {len(issues)}.")

        return {
            "status": final_status,
            "issues": issues
        }