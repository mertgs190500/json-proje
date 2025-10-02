import json
import jsonschema
from jsonschema import validate
import logging
import operator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(filename):
    """Loads a JSON file with UTF-8 encoding."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Dosya bulunamadı: {filename}")
        return None
    except json.JSONDecodeError:
        logging.error(f"JSON formatı geçersiz: {filename}")
        return None

def validate_against_schema(data, schema, schema_name="Genel"):
    """Validates data against a given JSON schema."""
    try:
        validate(instance=data, schema=schema, format_checker=jsonschema.FormatChecker())
        logging.info(f"DOĞRULAMA BAŞARILI: Veri yapısı '{schema_name}' şemasına uygun.")
        return True
    except jsonschema.exceptions.ValidationError as err:
        logging.error(f"DOĞRULAMA HATASI ({schema_name}): {err.message}")
        return False

class RuleEngine:
    """Evaluates declarative rules from rule_definitions.json."""
    def __init__(self):
        self.operators = {
            "equal": operator.eq,
            "greaterThan": operator.gt,
            "lessThan": operator.lt,
        }
        rules_data = load_json("rule_definitions.json")
        self.rulesets = rules_data.get("rulesets", {}) if rules_data else {}
        logging.info("Kural Motoru başlatıldı ve kurallar yüklendi.")

    def evaluate(self, ruleset_name, facts):
        """Evaluates a specific ruleset against given facts."""
        if ruleset_name not in self.rulesets:
            logging.error(f"Kural seti bulunamadı: {ruleset_name}")
            return False

        logic = self.rulesets[ruleset_name].get("logic", {})
        conditions = logic.get("conditions", {}).get("all", [])

        if not conditions:
            return True  # No conditions means the rule passes (e.g., AlwaysRun)

        for condition in conditions:
            fact_name = condition.get("fact")
            op_name = condition.get("operator")
            expected_value = condition.get("value")
            actual_value = facts.get(fact_name)

            if op_name not in self.operators:
                logging.error(f"Bilinmeyen operatör: {op_name}")
                return False

            op_func = self.operators[op_name]
            try:
                if not op_func(actual_value, expected_value):
                    return False
            except (TypeError, ValueError) as e:
                logging.error(f"Kural değerlendirme hatası (Tip Uyuşmazlığı). Fact: {fact_name}, Actual: {actual_value}, Expected: {expected_value}. Hata: {e}")
                return False
        return True

import importlib.util # For dynamic module loading

class ProfileManager:
    """Loads and manages inheritable profiles from csv_profiles.json."""
    def __init__(self):
        profiles_data = load_json("csv_profiles.json")
        self.profiles = profiles_data.get("profiles", {}) if profiles_data else {}
        logging.info("Profil Yöneticisi başlatıldı.")

    def get_merged_profile(self, profile_name):
        """Merges a specific profile with its base profile using inheritance."""
        if profile_name not in self.profiles:
            logging.error(f"Profil bulunamadı: {profile_name}")
            return None

        profile = self.profiles[profile_name].copy()
        base_name = profile.get("inherits")

        if base_name and base_name in self.profiles:
            base_profile = self.profiles[base_name].copy()
            # The specific profile's values overwrite the base profile's values
            merged = {**base_profile, **profile}
            return merged
        return profile

class DBManager:
    """Manages interactions with the flat-file JSON database."""
    def load_db(self, filename):
        """Loads a JSON database file."""
        logging.info(f"Veritabanı yükleniyor: {filename}")
        return load_json(filename)

    def save_db(self, filename, data):
        """Saves data to a JSON database file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Veritabanı başarıyla kaydedildi: {filename}")
        except Exception as e:
            logging.error(f"Veritabanı kaydedilemedi: {filename}. Hata: {e}")

class WorkflowOrchestrator:
    """Orchestrates the entire workflow based on a configuration file."""
    def __init__(self):
        self.policy = self._load_policy("orchestrator_policy.json")
        # Configure logging based on the policy
        log_level = self.policy.get("logging", {}).get("level", "INFO").upper()
        logging.getLogger().setLevel(log_level)

        self.workflow_schema = load_json("workflow_schema_v2.json")
        contracts_data = load_json("data_contracts.json")
        self.contracts = contracts_data.get("contracts", {}) if contracts_data else {}
        self.context = {}
        self.rule_engine = RuleEngine()
        self.profile_manager = ProfileManager()
        self.db_manager = DBManager() # Initialize the DB Manager
        logging.info("Orkestratör başlatıldı, Politikalar, DB Yöneticisi ve Veri Sözleşmeleri yüklendi.")

    def _load_policy(self, policy_file):
        """Loads operational policies from the specified file."""
        policy_data = load_json(policy_file)
        if not policy_data:
            logging.warning(f"Politika dosyası bulunamadı veya boş: {policy_file}. Varsayılan politikalar kullanılıyor.")
            # Return safe defaults
            return {
                "execution": {"stop_on_error": True, "stop_on_contract_violation": True},
                "logging": {"level": "INFO"}
            }
        return policy_data

    def validate_data_contract(self, contract_name, data):
        """Validates output data against a specified data contract."""
        if contract_name not in self.contracts:
            logging.error(f"Veri sözleşmesi bulunamadı: {contract_name}")
            return False

        contract_schema = self.contracts[contract_name]
        logging.info(f"Sözleşme doğrulanıyor: {contract_name}")
        return validate_against_schema(data, contract_schema, contract_name)

    def load_module(self, module_file):
        """Dynamically loads and instantiates a class from a Python module."""
        try:
            module_name = module_file.replace('.py', '')
            class_name = "".join(word.capitalize() for word in module_name.split('_'))

            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return getattr(module, class_name)()
        except Exception as e:
            logging.error(f"Modül yüklenemedi: {module_file}. Hata: {e}")
            return None

    def resolve_inputs(self, inputs, context):
        """Resolves $ref and $profile pointers in the input definitions."""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, dict):
                if "$ref" in value:
                    ref_path = value["$ref"]
                    if ref_path.startswith("context."):
                        try:
                            temp_context = context
                            for part in ref_path.split('.')[1:]:
                                temp_context = temp_context[part]
                            resolved[key] = temp_context
                            logging.info(f"Referans ($ref) çözümlendi: '{ref_path}'")
                        except (KeyError, TypeError):
                            logging.warning(f"Referans ($ref) çözümlenemedi: {ref_path}")
                            resolved[key] = None
                    else:
                        resolved[key] = value
                elif "$profile" in value:
                    # NEW: Resolve $profile references
                    profile_name = value["$profile"]
                    merged_profile = self.profile_manager.get_merged_profile(profile_name)
                    if merged_profile:
                        # The key for the resolved profile is the same as the input key
                        resolved[key] = merged_profile
                        logging.info(f"Profil ($profile) çözümlendi: '{profile_name}'")
                    else:
                        logging.warning(f"Profil ($profile) çözümlenemedi: {profile_name}")
                        resolved[key] = None
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved

    def run(self, config_file):
        """Loads and executes the workflow from a configuration file."""
        config_data = load_json(config_file)
        if not config_data:
            return

        # 1. Validate schema
        if not (self.workflow_schema and validate_against_schema(config_data, self.workflow_schema, "Workflow Schema V2")):
            logging.error("İş akışı başlatılamadı (Şema doğrulaması başarısız).")
            return

        logging.info(f"İş akışı başlatılıyor: {config_data['workflow_id']}")

        # 2. Step Execution Loop
        for step in config_data.get("steps", []):
            step_id = step.get('id', 'N/A')
            logging.info(f"--- Adım: {step_id} ---")

            # 2a. Evaluate Rules
            ruleset_name = step.get("rs", {}).get("ruleset_name")
            if not self.rule_engine.evaluate(ruleset_name, self.context):
                logging.info(f"Adım {step_id} atlandı (Kurallar geçmedi).")
                continue

            # 2b. Load Module
            module_instance = self.load_module(step["module"])
            if not module_instance:
                if self.policy.get("execution", {}).get("stop_on_error", True):
                    logging.error("Politika gereği (stop_on_error=True) modül yüklenemediği için iş akışı durduruluyor.")
                    break
                else:
                    continue

            # 2c. Prepare and Resolve Inputs
            raw_inputs = step.get("i", {})
            resolved_inputs = self.resolve_inputs(raw_inputs, self.context)

            # 2d. Execute Module
            try:
                # Standardized execution: All modules receive inputs, context, and the db_manager
                output = module_instance.execute(resolved_inputs, self.context, self.db_manager)
            except Exception as e:
                logging.error(f"Adım {step_id} yürütülürken hata: {e}")
                if self.policy.get("execution", {}).get("stop_on_error", True):
                    logging.error("Politika gereği (stop_on_error=True) iş akışı durduruluyor.")
                    break
                else:
                    continue

            # 2e. Validate Output Contract
            contract_name = step.get("o", {}).get("contract")
            is_contract_valid = True
            if contract_name:
                is_contract_valid = self.validate_data_contract(contract_name, output)

            if not is_contract_valid:
                logging.error(f"Adım {step_id} başarısız oldu (Sözleşme ihlali).")
                if self.policy.get("execution", {}).get("stop_on_contract_violation", True):
                    logging.error("Politika gereği (stop_on_contract_violation=True) iş akışı durduruluyor.")
                    break
                else:
                    continue

            # 2f. Update Context
            context_key = step.get("o", {}).get("context_key")
            if context_key:
                self.context[context_key] = output
                logging.info(f"'{context_key}' anahtarı context'e eklendi.")

            logging.info(f"Adım {step_id} tamamlandı.")

if __name__ == "__main__":
    # This block now runs the final, end-to-end workflow configuration.

    # Ensure a clean knowledge base for the run.
    # A real run might persist this, but for a clean test, we start fresh.
    with open("knowledge_base.json", "w", encoding='utf-8') as f:
        json.dump({"keyword_performance_weights": {}}, f)

    orchestrator = WorkflowOrchestrator()
    print("--- Final End-to-End Workflow Verification ---")
    orchestrator.run("finalv2_config.json")

    print("\n--- Workflow Complete. Final Context: ---")
    print(json.dumps(orchestrator.context, indent=2, ensure_ascii=False))

    print("\n--- Final State of Knowledge Base: ---")
    with open("knowledge_base.json", "r", encoding='utf-8') as f:
        final_kb = json.load(f)
        print(json.dumps(final_kb, indent=2, ensure_ascii=False))

    # Clean up dummy files created during the run
    import os
    if os.path.exists("knowledge_base.json"):
        os.remove("knowledge_base.json")
    if os.path.exists("finalv2_config.json"):
        os.remove("finalv2_config.json")
    if os.path.exists("images"):
        import shutil
        shutil.rmtree("images")