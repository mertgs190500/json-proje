import json
import jsonschema
from jsonschema import validate
import logging
import operator
import importlib.util
import os
import glob
from session_manager import SessionManager

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- UTILITY FUNCTIONS ---
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

# --- CORE CLASSES ---
class RuleEngine:
    """Evaluates declarative rules from rule_definitions.json."""
    def __init__(self):
        self.operators = {"equal": operator.eq, "greaterThan": operator.gt, "lessThan": operator.lt}
        rules_data = load_json("rule_definitions.json")
        self.rulesets = rules_data.get("rulesets", {}) if rules_data else {}
        logging.info("Kural Motoru başlatıldı ve kurallar yüklendi.")

    def evaluate(self, ruleset_name, facts):
        """Evaluates a specific ruleset against given facts."""
        if not ruleset_name:
            logging.warning("Kural seti adı belirtilmemiş, atlanıyor.")
            return False # Should not proceed if rule name is missing
        if ruleset_name not in self.rulesets:
            logging.error(f"Kural seti bulunamadı: {ruleset_name}")
            return False
        logic = self.rulesets[ruleset_name].get("logic", {})
        conditions = logic.get("conditions", {}).get("all", [])
        if not conditions: return True
        for condition in conditions:
            fact_name, op_name, expected_value = condition.get("fact"), condition.get("operator"), condition.get("value")
            actual_value = facts.get(fact_name)
            if op_name not in self.operators:
                logging.error(f"Bilinmeyen operatör: {op_name}"); return False
            try:
                if not self.operators[op_name](actual_value, expected_value): return False
            except (TypeError, ValueError) as e:
                logging.error(f"Kural değerlendirme hatası (Tip Uyuşmazlığı). Fact: {fact_name}, Hata: {e}"); return False
        return True

class ProfileManager:
    """Loads and manages inheritable profiles from csv_profiles.json."""
    def __init__(self):
        profiles_data = load_json("csv_profiles.json")
        self.profiles = profiles_data.get("profiles", {}) if profiles_data else {}
        logging.info("Profil Yöneticisi başlatıldı.")

    def get_merged_profile(self, profile_name):
        """Merges a specific profile with its base profile using inheritance."""
        if profile_name not in self.profiles:
            logging.error(f"Profil bulunamadı: {profile_name}"); return None
        profile = self.profiles[profile_name].copy()
        base_name = profile.get("inherits")
        if base_name and base_name in self.profiles:
            base_profile = self.profiles[base_name].copy()
            return {**base_profile, **profile}
        return profile

class DBManager:
    """Manages interactions with the flat-file JSON database."""
    def load_db(self, filename): return load_json(filename)
    def save_db(self, filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Veritabanı başarıyla kaydedildi: {filename}")
        except Exception as e:
            logging.error(f"Veritabanı kaydedilemedi: {filename}. Hata: {e}")

class WorkflowOrchestrator:
    """Orchestrates the entire workflow based on a configuration file or dictionary."""
    def __init__(self):
        self.policy = load_json("orchestrator_policy.json") or {}
        logging.getLogger().setLevel(self.policy.get("logging", {}).get("level", "INFO").upper())
        self.session = SessionManager(self.policy.get("session"))
        self.workflow_schema = load_json("workflow_schema_v2.json")
        self.contracts = (load_json("data_contracts.json") or {}).get("contracts", {})
        self.context = {}
        self.state = "IDLE"
        self.rule_engine = RuleEngine()
        self.profile_manager = ProfileManager()
        self.db_manager = DBManager()
        logging.info("Orkestratör başlatıldı.")

    def validate_data_contract(self, contract_name, data):
        if contract_name not in self.contracts:
            logging.error(f"Veri sözleşmesi bulunamadı: {contract_name}"); return False
        logging.info(f"Sözleşme doğrulanıyor: {contract_name}")
        return validate_against_schema(data, self.contracts[contract_name], contract_name)

    def load_module(self, module_file):
        try:
            module_name = module_file.replace('.py', '')
            class_name = "".join(word.capitalize() for word in module_name.split('_'))
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, class_name)()
        except Exception as e:
            logging.error(f"Modül yüklenemedi: {module_file}. Hata: {e}"); return None

    def resolve_inputs(self, inputs, context):
        if isinstance(inputs, dict):
            if "$ref" in inputs:
                ref_path = inputs["$ref"]
                try:
                    val = context
                    for part in ref_path.split('.')[1:]: val = val[part]
                    logging.info(f"Referans ($ref) çözümlendi: '{ref_path}'")
                    return val
                except (KeyError, TypeError) as e:
                    logging.warning(f"Referans ($ref) çözümlenemedi: {ref_path}. Hata: {e}"); return None
            if "$profile" in inputs:
                profile_name = inputs["$profile"]
                logging.info(f"Profil ($profile) çözümleniyor: '{profile_name}'")
                return self.profile_manager.get_merged_profile(profile_name)
            return {k: self.resolve_inputs(v, context) for k, v in inputs.items()}
        elif isinstance(inputs, list):
            return [self.resolve_inputs(item, context) for item in inputs]
        return inputs

    def run(self, config):
        """Loads and executes the workflow from a configuration file path or a dictionary."""
        if self.state == "WORKING":
            logging.error("Orkestratör zaten çalışıyor. Yeni görev reddedildi.")
            return

        self.state = "WORKING"
        try:
            if isinstance(config, str):
                config_data = load_json(config)
            elif isinstance(config, dict):
                config_data = config
            else:
                logging.error("Geçersiz yapılandırma. Dosya yolu (str) veya sözlük (dict) olmalıdır.")
                return

            if not config_data:
                logging.error("İş akışı yapılandırması yüklenemedi.")
                return
            if self.workflow_schema and not validate_against_schema(config_data, self.workflow_schema, "Workflow Schema V2"):
                 logging.error("İş akışı şema doğrulaması başarısız oldu.")
                 return

            logging.info(f"İş akışı başlatılıyor: {config_data.get('workflow_id', 'N/A')}")
            for step in config_data.get("steps", []):
                step_id = step.get('id', 'N/A')
                logging.info(f"--- Adım: {step_id} ---")

                status, msg = self.session.check_status()
                if status != "STATUS_OK":
                    logging.error(f"İş akışı durduruldu (Session: {status}): {msg}")
                    break

                ruleset_name = step.get("rs", {}).get("ruleset_name")
                if ruleset_name and not self.rule_engine.evaluate(ruleset_name, self.context):
                    logging.info(f"Adım {step_id} atlandı (Kural '{ruleset_name}' geçmedi).")
                    continue

                module_instance = self.load_module(step["module"])
                if not module_instance:
                    if self.policy.get("execution", {}).get("stop_on_error", True):
                        break
                    else:
                        continue

                resolved_inputs = self.resolve_inputs(step.get("i", {}), self.context)
                try:
                    output = module_instance.execute(resolved_inputs, self.context, self.db_manager)
                except Exception as e:
                    logging.error(f"Adım {step_id} yürütülürken hata: {e}", exc_info=True)
                    if self.policy.get("execution", {}).get("stop_on_error", True):
                        break
                    else:
                        continue

                contract_name = step.get("o", {}).get("contract")
                if contract_name and not self.validate_data_contract(contract_name, output):
                    if self.policy.get("execution", {}).get("stop_on_contract_violation", True):
                        break
                    else:
                        continue

                context_key = step.get("o", {}).get("context_key")
                if context_key:
                    self.context[context_key] = output
                    logging.info(f"'{context_key}' anahtarı context'e eklendi.")

                self.session.log_update()
                logging.info(f"Adım {step_id} tamamlandı.")
        finally:
            self.state = "IDLE"
            logging.info("Orkestratör durumu 'IDLE' olarak ayarlandı.")

if __name__ == "__main__":
    logging.info("CSV INGESTION PROCESS (CSV-INGEST-PROCESS-01) BAŞLATILIYOR...")

    file_profile_map = {
        "Similar_keywords*.csv": "similar_keywords_v2",
        "Top_listings*.csv": "top_listings_title_first_v1",
        "Listings*.csv": "listings_title_first_v1"
    }

    files_to_process = [f for pattern in file_profile_map for f in glob.glob(f"./{pattern}")]

    if not files_to_process:
        logging.warning("Kök dizinde işlenecek CSV dosyası bulunamadı. (Örn: Similar_keywords*.csv)")
    else:
        logging.info(f"İşlenecek dosyalar bulundu: {files_to_process}")
        orchestrator = WorkflowOrchestrator()

        for file_path in files_to_process:
            profile_name = next((p for pattern, p in file_profile_map.items() if glob.fnmatch.fnmatch(os.path.basename(file_path), pattern)), None)
            if not profile_name:
                logging.warning(f"'{file_path}' için uygun profil bulunamadı. Atlanıyor.")
                continue

            logging.info(f"\n>>> '{os.path.basename(file_path)}' için iş akışı başlatılıyor (Profil: {profile_name}) <<<")

            dynamic_workflow = {
                "workflow_id": f"ingest_{os.path.basename(file_path)}",
                "steps": [
                    {
                        "id": f"load_{os.path.basename(file_path)}",
                        "name": f"Load CSV: {os.path.basename(file_path)}",
                        "module": "data_loader.py",
                        "i": {"file_path": file_path},
                        "o": {"context_key": "current_csv_data"},
                        "rs": {"ruleset_name": "AlwaysRun"},
                        "meta": {
                            "description": "Loads the raw content of a CSV file for processing.",
                            "author": "Jules",
                            "last_updated": "2025-10-02T12:00:00Z"
                        }
                    },
                    {
                        "id": f"ingest_{os.path.basename(file_path)}",
                        "name": f"Ingest CSV: {os.path.basename(file_path)}",
                        "module": "csv_ingestor.py",
                        "i": {
                            "raw_content": {"$ref": "context.current_csv_data.raw_content"},
                            "file_path": {"$ref": "context.current_csv_data.file_path"},
                            "resolved_profile": {"$profile": profile_name}
                        },
                        "o": {"context_key": f"processed_{os.path.basename(file_path)}"},
                        "rs": {"ruleset_name": "AlwaysRun"},
                        "meta": {
                            "description": "Parses, cleans, and validates CSV data using a profile.",
                            "author": "Jules",
                            "last_updated": "2025-10-02T12:00:00Z"
                        }
                    }
                ]
            }
            orchestrator.run(dynamic_workflow)

        logging.info("\n--- TÜM CSV İŞLEME AKIŞLARI TAMAMLANDI ---")
        print("\n--- Final Context Özeti: ---")
        final_context_summary = {}
        for key, value in orchestrator.context.items():
            if key.startswith("processed_") and isinstance(value, dict):
                final_context_summary[key] = {
                    "status": value.get('status'),
                    "message": value.get('message'),
                    "processed_rows": len(value.get('data', [])) if value.get('data') is not None else 0,
                }
        print(json.dumps(final_context_summary, indent=2, ensure_ascii=False))