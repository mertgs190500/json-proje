import logging
import pandas as pd
from datetime import datetime, timezone
from version_control import VersionControl

class FeedbackProcessor:
    """
    Analyzes post-publication performance data, generates a report, and updates
    the project's knowledge base with new learnings.
    """

    def execute(self, inputs: dict, context: dict, knowledge_manager, db_manager=None) -> dict:
        """
        Executes the feedback processing logic.

        Args:
            inputs (dict): Contains 'performance_data_csv' path.
            context (dict): The shared context, must contain 'fs.ver' for versioning.
            knowledge_manager: An instance of the KnowledgeManager.
            db_manager: (Optional) A database manager instance.

        Returns:
            dict: A dictionary containing the status and a summary of the operation.
        """
        logging.info("[FeedbackProcessor] Starting feedback processing.")

        performance_data_path = inputs.get("performance_data_csv")
        if not performance_data_path or not knowledge_manager:
            logging.error("[FeedbackProcessor] Missing required inputs: 'performance_data_csv' or 'knowledge_manager'.")
            return {"status": "failed", "reason": "Missing required inputs."}

        try:
            perf_df = pd.read_csv(performance_data_path, encoding='latin-1')
        except FileNotFoundError as e:
            logging.error(f"[FeedbackProcessor] File not found: {e}")
            return {"status": "failed", "reason": f"File not found: {e.filename}"}
        except Exception as e:
            logging.error(f"[FeedbackProcessor] An error occurred during data loading: {e}", exc_info=True)
            return {"status": "failed", "reason": str(e)}

        insights_added = 0
        processed_rows = 0
        failed_rows = 0

        for index, row in perf_df.iterrows():
            processed_rows += 1
            try:
                visits = row.get('visits', 0)
                orders = row.get('orders', 0)
                ad_spend = row.get('ad_spend', 0.0)
                revenue = row.get('revenue', 0.0)
                title = row.get('title', '')
                tags = str(row.get('tags', '')).split(',')

                conversion_rate = (orders / visits) if visits > 0 else 0
                roas = (revenue / ad_spend) if ad_spend > 0 else 0

                if ad_spend > 10:
                    for tag in filter(None, [t.strip().lower() for t in tags]):
                        confidence = 0.85 if ad_spend > 50 else 0.70
                        if roas > 2.0:
                            knowledge_manager.add_insight(key="keyword_roas", value={"keyword": tag, "roas": round(roas, 2), "is_successful": True}, source_id="FEEDBACK-LOOP-01", confidence=confidence)
                            insights_added += 1
                        elif roas < 0.8:
                            knowledge_manager.add_insight(key="keyword_roas", value={"keyword": tag, "roas": round(roas, 2), "is_successful": False}, source_id="FEEDBACK-LOOP-01", confidence=confidence)
                            insights_added += 1

                if visits > 100:
                    confidence = 0.90 if visits > 1000 else 0.75
                    if any(char.isdigit() for char in title):
                        if conversion_rate > 0.02:
                            knowledge_manager.add_insight(key="title_structure_contains_number", value={"has_number": True, "conversion_rate": round(conversion_rate, 4), "is_successful": True}, source_id="FEEDBACK-LOOP-01", confidence=confidence)
                            insights_added += 1
                        elif conversion_rate < 0.005:
                            knowledge_manager.add_insight(key="title_structure_contains_number", value={"has_number": True, "conversion_rate": round(conversion_rate, 4), "is_successful": False}, source_id="FEEDBACK-LOOP-01", confidence=confidence)
                            insights_added += 1

            except Exception as e:
                logging.warning(f"[FeedbackProcessor] Could not process row {index}: {e}")
                failed_rows += 1
                continue

        logging.info(f"[FeedbackProcessor] Processing complete. Added {insights_added} new insights.")

        report_data = {
            "status": "success",
            "message": f"Feedback processing complete. {insights_added} new insights added.",
            "insights_added": insights_added,
            "rows_processed": processed_rows,
            "rows_failed": failed_rows,
            "source_file": performance_data_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            vc_config = context.get('fs', {}).get('ver')
            if not vc_config:
                logging.error("[FeedbackProcessor] Versioning configuration ('fs.ver') not found in context.")
                report_data['status'] = 'warning'
                report_data['message'] += " | WARNING: Versioning config missing, report not saved."
            else:
                vc = VersionControl(versioning_config=vc_config)
                save_result = vc.save_with_metadata(
                    base_path='outputs/performance_feedback_report.json',
                    data=report_data,
                    actor='feedback_processor.py',
                    reason='Processed listing performance feedback and generated report.'
                )
                report_data['artefact'] = save_result
                logging.info("[FeedbackProcessor] Successfully saved performance feedback report.")

        except Exception as e:
            logging.error(f"[FeedbackProcessor] Failed to save performance feedback report: {e}", exc_info=True)
            report_data['status'] = 'warning'
            report_data['message'] += f" | WARNING: Failed to save report via VersionControl: {e}"

        return report_data