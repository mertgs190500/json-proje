import logging

class ListingAssembler:
    """
    Assembles all individual content pieces (title, description, tags, etc.)
    into a single, final listing object ready for export.
    """

    def execute(self, inputs, context, db_manager=None):
        """
        Main execution method. It combines all provided data into a structured object.

        Args:
            inputs (dict): A dictionary containing all the generated content pieces
                           from previous steps, e.g., {'title_data': ..., 'tags_data': ...}.

        Returns:
            dict: A dictionary containing the 'final_listing_object'.
        """
        logging.info("[ListingAssembler] Assembling final listing object.")

        # This structure should be compatible with the export columns defined in finalv1.json (/exp/cols)
        final_listing = {
            "sku": inputs.get("product_sku", "SKU-001"),
            "title": inputs.get("title_data", {}).get("title", ""),
            "description": inputs.get("description_data", {}).get("formatted_description", ""),
            "tags": inputs.get("tags_data", {}).get("final_tags", []),
            "attributes": inputs.get("packaging_strategy", {}).get("attributes", {}),
            "pricing": inputs.get("product_data", {}).get("pricing", {}),
            "shipping_profile_id": inputs.get("shop_policies", {}).get("shipping_profile_id", "default_shipping"),
            "image_paths": inputs.get("visual_data", {}).get("image_paths", []),
            "metadata": {
                "compliance_status": inputs.get("compliance_report", {}).get("status", "UNKNOWN"),
                "source_workflow_id": context.get("workflow_id", "unknown_workflow")
            }
        }

        # Perform a final check for completeness
        if not final_listing["title"] or not final_listing["description"] or not final_listing["tags"]:
            logging.warning("[ListingAssembler] Final assembly has missing core components (title, desc, or tags).")

        logging.info("[ListingAssembler] Final listing object assembled successfully.")

        return {"final_listing_object": final_listing}