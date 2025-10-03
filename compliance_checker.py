import re
import logging
from version_control import VersionControl

class ComplianceChecker:
    """
    Checks SEO content against a set of compliance rules defined in the project configuration.
    """

    def _get_ruleset(self, context):
        """
        Safely retrieves the ruleset from the context.
        The orchestrator is expected to resolve any $refs and place the
        ruleset at the specified path.
        """
        try:
            # Path confirmed in previous step: /run/s/14/rs/ruleset
            ruleset = context['run']['s']['14']['rs']['ruleset']
            if not isinstance(ruleset, list):
                return None, f"Ruleset at '/run/s/14/rs/ruleset' is not a list."
            return ruleset, None
        except KeyError:
            return None, "Compliance ruleset not found at context path '/run/s/14/rs/ruleset'."
        except Exception as e:
            return None, f"An unexpected error occurred while accessing the ruleset: {e}"

    def execute(self, inputs, context, knowledge_manager=None):
        """
        Executes the compliance checks.

        Args:
            inputs (dict): A dictionary containing the content to check.
                           Expected keys: 'title', 'description', 'tags'.
            context (dict): The workflow context, containing configuration and rules.
            db_manager: The database manager (not used in this module).

        Returns:
            dict: A dictionary with the compliance check results.
                  {'status': 'PASS'|'FAIL', 'issues': [...]}.
        """
        title = inputs.get('title', '')
        description = inputs.get('description', '')
        tags = inputs.get('tags', [])

        # For case-insensitive checks
        tags_str_lower = ' '.join(map(str, tags)).lower()
        full_text_lower = f"{title.lower()} {description.lower()} {tags_str_lower}"

        # For case-sensitive checks (like ALL CAPS)
        all_text_for_caps_check = f"{title} {description}"

        issues = []

        ruleset, error_msg = self._get_ruleset(context)
        if error_msg:
            result = {'status': 'FAIL', 'issues': [{'rule_id': 'LOAD_ERROR', 'message': error_msg}]}
        else:
            for rule in ruleset:
                rule_id = rule.get('id')
                params = rule.get('prm', {})

                if rule_id == 'NO_BANNED_TERMS':
                    banned_list = params.get('list', [])
                    for term in banned_list:
                        if re.search(r'\b' + re.escape(term.lower()) + r'\b', full_text_lower):
                            issues.append({
                                'rule_id': rule_id,
                                'message': f"Forbidden term found: '{term}'"
                            })

                elif rule_id == 'NO_ALLCAPS_SPAM':
                    # FIX: This check now runs on the original case-sensitive text.
                    words = re.findall(r'\b[A-Z]{3,}\b', all_text_for_caps_check)
                    if words:
                        issues.append({
                            'rule_id': rule_id,
                            'message': f"Potential ALL CAPS spam detected. Words: {', '.join(words)}"
                        })

                elif rule_id == 'NO_MISLEADING_CLAIMS':
                    claims = params.get('claims', [])
                    for claim in claims:
                        if re.search(r'\b' + re.escape(claim.lower()) + r'\b', full_text_lower):
                            issues.append({
                                'rule_id': rule_id,
                                'message': f"Potentially misleading claim found: '{claim}'"
                            })

            if issues:
                result = {'status': 'FAIL', 'issues': issues}
            else:
                result = {'status': 'PASS', 'issues': []}

        # Save the report using VersionControl
        if isinstance(knowledge_manager, VersionControl):
            try:
                knowledge_manager.save_with_metadata(
                    base_path='outputs/compliance_report.json',
                    data=result,
                    actor='compliance_checker.py',
                    reason='Generated compliance report for the listing content.'
                )
                logging.info("[ComplianceChecker] Successfully saved compliance report with metadata.")
            except Exception as e:
                logging.error(f"[ComplianceChecker] Failed to save report using version control: {e}", exc_info=True)

        return result