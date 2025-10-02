import json
import jsonschema
from jsonschema import validate
import logging
import operator
import importlib.util
import os

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json(filename):
    """Safely loads a JSON file with error handling."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in file: {filename}")
        return None

class DBManager:
    """Manages the knowledge base, a simple JSON file acting as a database."""
    def __init__(self, db_file):
        self.db_file = db_file
        self.data = self._load_db()

    def _load_db(self):
        """Loads the database from the JSON file."""
        if os.path.exists(self.db_file):
            return load_json(self.db_file)
        logging.warning(f"Knowledge base file '{self.db_file}' not found. Starting with an empty one.")
        return {}

    def get(self, key, default=None):
        """Gets a value from the database."""
        return self.data.get(key, default)

    def save(self):
        """Saves the current state of the data back to the JSON file."""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            logging.info(f"Knowledge base saved to {self.db_file}")
        except IOError as e:
            logging.error(f"Could not write to knowledge base file {self.db_file}: {e}")

class ProfileManager:
    """Manages loading and resolving of processing profiles."""
    def __init__(self, profiles_file):
        self.profiles = load_json(profiles_file) or {}

    def get_profile(self, name):
        """Gets a profile by name, resolving any inheritance."""
        if name not in self.profiles:
            logging.error(f"Profile '{name}' not found.")
            return None

        profile = self.profiles[name]
        if "inherits" in profile:
            parent_name = profile["inherits"]
            parent_profile = self.get_profile(parent_name)
            if parent_profile:
                # Parent's keys are overridden by child's keys
                merged_profile = parent_profile.copy()
                merged_profile.update(profile)
                # We can remove 'inherits' after processing it
                del merged_profile["inherits"]
                # Cache the resolved profile for future speed
                self.profiles[name] = merged_profile
                return merged_profile
        return profile

class WorkflowOrchestrator:
    """Orchestrates the workflow by executing a series of configured steps."""
    def __init__(self, knowledge_base_file="project_core/knowledge_base.json"):
        self.context = {}
        self.db_manager = DBManager(knowledge_base_file)
        # Assuming config files are in the same directory or have paths relative to the script's location
        self.profile_manager = ProfileManager("project_core/csv_profiles.json")
        self.contracts = load_json("project_core/data_contracts.json") or {}

    def _resolve_value(self, value):
        """Resolves references from context or profiles."""
        if isinstance(value, str):
            if value.startswith('$ref.'):
                # Resolve from context, e.g., $ref.step1.output.data
                keys = value.split('.')[1:]
                resolved_value = self.context
                for key in keys:
                    if isinstance(resolved_value, dict):
                        resolved_value = resolved_value.get(key)
                    else:
                        logging.warning(f"Cannot resolve key '{key}' in non-dict: {resolved_value}")
                        return None
                return resolved_value
            elif value.startswith('$profile.'):
                # Resolve from profile manager, e.g., $profile.my_csv_profile
                profile_name = value.split('.')[1:]
                return self.profile_manager.get_profile(profile_name[0])
        elif isinstance(value, dict):
            # Recursively resolve values in a dictionary
            return {k: self._resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            # Recursively resolve values in a list
            return [self._resolve_value(item) for item in value]
        return value

    def _validate_with_contract(self, data, contract_name):
        """Validates data against a predefined contract."""
        if contract_name not in self.contracts:
            logging.warning(f"Contract '{contract_name}' not found. Skipping validation.")
            return True

        schema = self.contracts[contract_name]
        try:
            validate(instance=data, schema=schema)
            logging.info(f"Data for '{contract_name}' successfully validated.")
            return True
        except jsonschema.exceptions.ValidationError as err:
            logging.error(f"Contract validation failed for '{contract_name}': {err.message}")
            return False

    def run(self, config_file):
        """Runs the entire workflow based on the configuration file."""
        config = load_json(config_file)
        if not config:
            logging.critical("Workflow configuration could not be loaded. Aborting.")
            return

        for step in config.get("workflow", []):
            step_name = step["name"]
            module_name = step["module"]
            class_name = step["class"]
            inputs = self._resolve_value(step.get("inputs", {}))

            logging.info(f"--- Executing Step: {step_name} ---")

            try:
                # Dynamically import the module
                module_path = f"project_core/{module_name}.py"
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Instantiate the class and execute
                BusinessLogicClass = getattr(module, class_name)
                instance = BusinessLogicClass()

                # Pass db_manager to execute method
                output = instance.execute(inputs=inputs, context=self.context, db_manager=self.db_manager)

                # Validate and store output
                if "contract" in step and not self._validate_with_contract(output, step["contract"]):
                    logging.error(f"Step {step_name} failed validation. Aborting workflow.")
                    break

                self.context[step_name] = {"output": output}
                logging.info(f"Step '{step_name}' executed successfully.")

            except Exception as e:
                logging.critical(f"An error occurred during step '{step_name}': {e}", exc_info=True)
                break

        self.db_manager.save()

if __name__ == "__main__":
    # Per user instruction, using finalv1.json as the knowledge base file.
    # This might need to be changed to knowledge_base.json later.
    orchestrator = WorkflowOrchestrator(knowledge_base_file="project_core/finalv1.json")
    orchestrator.run("project_core/finalv2_config.json")
    print("\nWorkflow Finished. Final Context:")
    print(json.dumps(orchestrator.context, indent=2, ensure_ascii=False))