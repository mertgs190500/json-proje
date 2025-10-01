import json
import jsonschema
from jsonschema import validate
import logging
import operator
import importlib.util

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(filename):
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
    try:
        validate(instance=data, schema=schema, format_checker=jsonschema.FormatChecker())
        logging.info(f"DOĞRULAMA BAŞARILI: Veri yapısı '{schema_name}' şemasına uygun.")
        return True
    except jsonschema.exceptions.ValidationError as err:
        logging.error(f"DOĞRULAMA HATASI ({schema_name}): {err.message}")
        return False

class RuleEngine:
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
        if ruleset_name not in self.rulesets:
            logging.error(f"Kural seti bulunamadı: {ruleset_name}")
            return False
        logic = self.rulesets[ruleset_name].get("logic", {})
        conditions = logic.get("conditions", {}).get("all", [])
        if not conditions:
            return True
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
                logging.error(f"Kural değerlendirme hatası. Fact: {fact_name}, Actual: {actual_value}, Expected: {expected_value}. Hata: {e}")
                return False
        return True

class WorkflowOrchestrator:
    def __init__(self):
        self.workflow_schema = load_json("workflow_schema_v2.json")
        contracts_data = load_json("data_contracts.json")
        self.contracts = contracts_data.get("contracts", {}) if contracts_data else {}
        self.context = {}
        self.rule_engine = RuleEngine()
        logging.info("Orkestratör başlatıldı ve Veri Sözleşmeleri yüklendi.")

    def validate_data_contract(self, contract_name, data):
        if contract_name not in self.contracts:
            logging.error(f"Veri sözleşmesi bulunamadı: {contract_name}")
            return False
        contract_schema = self.contracts[contract_name]
        logging.info(f"Sözleşme doğrulanıyor: {contract_name}")
        return validate_against_schema(data, contract_schema, contract_name)

    def load_module(self, module_file):
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
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, dict) and "$ref" in value:
                ref_path = value["$ref"]
                if ref_path.startswith("context."):
                    try:
                        temp_context = context
                        for part in ref_path.split('.')[1:]:
                            temp_context = temp_context[part]
                        resolved[key] = temp_context
                    except (KeyError, TypeError):
                        logging.warning(f"Referans çözümlenemedi: {ref_path}")
                        resolved[key] = None
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        return resolved

    def run(self, config_file):
        config_data = load_json(config_file)
        if not config_data:
            return
        if not (self.workflow_schema and validate_against_schema(config_data, self.workflow_schema, "Workflow Schema V2")):
            logging.error("İş akışı başlatılamadı (Şema doğrulaması başarısız).")
            return
        logging.info(f"İş akışı başlatılıyor: {config_data['workflow_id']}")
        for step in config_data["steps"]:
            step_id = step['id']
            logging.info(f"--- Adım: {step_id} ---")
            ruleset_name = step["rs"].get("ruleset_name")
            if not self.rule_engine.evaluate(ruleset_name, self.context):
                logging.info(f"Adım {step_id} atlandı (Kurallar geçmedi).")
                continue
            module_instance = self.load_module(step["module"])
            if not module_instance:
                break
            raw_inputs = step["i"]
            resolved_inputs = self.resolve_inputs(raw_inputs, self.context)
            try:
                output = module_instance.execute(resolved_inputs, self.context)
            except Exception as e:
                logging.error(f"Adım {step_id} yürütülürken hata: {e}")
                break
            contract_name = step["o"].get("contract")
            if contract_name and not self.validate_data_contract(contract_name, output):
                logging.error(f"Adım {step_id} başarısız oldu (Sözleşme ihlali). İş akışı durduruluyor.")
                break
            context_key = step["o"].get("context_key")
            if context_key:
                self.context[context_key] = output
            logging.info(f"Adım {step_id} tamamlandı.")

if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()
    orchestrator.run("finalv2_config.json")
    print("\nİş Akışı Tamamlandı. Son Bağlam (Context):")
    print(json.dumps(orchestrator.context, indent=2, ensure_ascii=False))