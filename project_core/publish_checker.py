import logging

class PublishChecker:
    """
    Verifies the final assembled listing against a pre-publish checklist.

    This class ensures that all critical conditions related to media, compliance,
    SEO, and data integrity are met before the product listing is marked as
    ready for publication. The rules for this checklist are defined in the
    main project configuration file.
    """

    def __init__(self, config):
        """
        Initializes the PublishChecker.

        Args:
            config (dict): The main configuration dictionary, which contains
                           rules and settings.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def _get_rules(self, context):
        """Safely retrieves the ruleset from the context."""
        try:
            # According to the task, rules are at /s/18/rls
            # Based on other modules, the orchestrator resolves this to 'run.s.18.rls'
            return context.get('run', {}).get('s', {}).get('18', {}).get('rls')
        except KeyError as e:
            self.logger.error(f"Could not retrieve rules from context: {e}")
            return None

    def _get_inputs(self, context):
        """Safely retrieves all necessary inputs from the context."""
        inputs = {
            'listing_status': context.get('listing', {}).get('status'),
            'export_file_path': context.get('export', {}).get('file_path'),
            'export_sha256': context.get('export', {}).get('sha256'),
            'compliance_status': context.get('compliance', {}).get('status'),
            'ads_sync_status': context.get('ads_sync', {}).get('status'),
            'media_manifest': context.get('listing', {}).get('final', {}).get('media', {}).get('manifest', [])
        }
        return inputs

    def execute(self, inputs, context, db_manager=None):
        """
        Executes the pre-publish checklist against the assembled listing.
        """
        checklist_results = []
        notes = []

        # Load rules and inputs
        rules = self._get_rules(context)
        if not rules:
            return {
                'publish_status': 'BLOCKED',
                'checklist_results': [],
                'notes': 'Configuration error: Could not load checklist rules for step 18.'
            }

        checklist_inputs = self._get_inputs(context)

        # Rule: Check listing assembly status
        if 'CHECK_LISTING_STATUS' in rules:
            status = checklist_inputs.get('listing_status')
            if status == 'PASS':
                checklist_results.append({'rule': 'CHECK_LISTING_STATUS', 'status': 'PASS'})
            else:
                checklist_results.append({'rule': 'CHECK_LISTING_STATUS', 'status': 'FAIL'})
                notes.append(f"Listing assembly status is '{status}', but must be 'PASS'.")

        # Rule: Check export file and hash
        if 'CHECK_EXPORT_ARTIFACTS' in rules:
            file_path = checklist_inputs.get('export_file_path')
            sha256 = checklist_inputs.get('export_sha256')
            if file_path and sha256:
                checklist_results.append({'rule': 'CHECK_EXPORT_ARTIFACTS', 'status': 'PASS'})
            else:
                checklist_results.append({'rule': 'CHECK_EXPORT_ARTIFACTS', 'status': 'FAIL'})
                notes.append(f"Export artifacts are incomplete. File path: '{file_path}', SHA256: '{sha256}'.")

        # Rule: Check compliance status
        if 'CHECK_COMPLIANCE_STATUS' in rules:
            status = checklist_inputs.get('compliance_status')
            if status == 'PASS':
                checklist_results.append({'rule': 'CHECK_COMPLIANCE_STATUS', 'status': 'PASS'})
            else:
                checklist_results.append({'rule': 'CHECK_COMPLIANCE_STATUS', 'status': 'FAIL'})
                notes.append(f"Compliance status is '{status}', but must be 'PASS'.")

        # Rule: Check Ads Sync status
        if 'CHECK_ADS_SYNC_STATUS' in rules:
            status = checklist_inputs.get('ads_sync_status')
            if status in ['PASS', 'WARN']:
                checklist_results.append({'rule': 'CHECK_ADS_SYNC_STATUS', 'status': 'PASS'})
            else:
                checklist_results.append({'rule': 'CHECK_ADS_SYNC_STATUS', 'status': 'FAIL'})
                notes.append(f"Ads sync status is '{status}', which is not allowed.")

        # Rule: Final Media Check
        if 'CHECK_MEDIA_MANIFEST' in rules:
            media_manifest = checklist_inputs.get('media_manifest')
            # Assuming a simple check for non-empty manifest
            if media_manifest and isinstance(media_manifest, list) and len(media_manifest) > 0:
                 checklist_results.append({'rule': 'CHECK_MEDIA_MANIFEST', 'status': 'PASS'})
            else:
                checklist_results.append({'rule': 'CHECK_MEDIA_MANIFEST', 'status': 'FAIL'})
                notes.append("Final media check failed; manifest is empty or invalid.")

        # Determine final publish status
        final_status = 'READY'
        if notes:
            final_status = 'BLOCKED'

        return {
            'publish_status': final_status,
            'checklist_results': checklist_results,
            'notes': " | ".join(notes)
        }