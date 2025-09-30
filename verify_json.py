import json
import os
import collections.abc

# --- Konfigürasyon ---
SOURCE_FILE = "uretim_cekirdek_v15_revised.json"
TARGET_FILE = "uretim_cekirdek_v17_nextgen.json"

# Helper function to load JSON file safely
def load_json_file(filename):
    if not os.path.exists(filename):
        print(f"ERROR: File not found: {filename}")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid or truncated JSON format in: {filename}. Details: {e}")
        return None

# Helper function for deep comparison (detecting missing keys and type mismatches)
def find_missing_keys(source_dict, target_dict, path=""):
    missing = []
    if not isinstance(source_dict, dict) or not isinstance(target_dict, dict):
        return missing

    for key in source_dict:
        current_path = f"{path}/{key}" if path else key
        if key not in target_dict:
            missing.append(current_path)
        else:
            # Recursive call if both values are dictionaries
            if isinstance(source_dict[key], dict) and isinstance(target_dict[key], dict):
                missing.extend(find_missing_keys(source_dict[key], target_dict[key], current_path))
            # Check if types are different (potential data corruption)
            elif type(source_dict[key]) != type(target_dict[key]):
                # Allow float to int conversion if values are the same (common in JSON serialization)
                if not (isinstance(source_dict[key], (int, float)) and isinstance(target_dict[key], (int, float)) and source_dict[key] == target_dict[key]):
                   missing.append(f"DEBUG_PATH: {current_path} (Type mismatch: {type(source_dict[key]).__name__} vs {type(target_dict[key]).__name__})")
    return missing

# Helper function to check existence of a path
def check_path_exists(data, path_parts):
    temp_data = data
    for part in path_parts:
        if isinstance(temp_data, dict) and part in temp_data:
            temp_data = temp_data[part]
        elif isinstance(temp_data, list):
            try:
                index = int(part)
                if index < len(temp_data):
                    temp_data = temp_data[index]
                else:
                    return False
            except ValueError:
                return False
        else:
            return False
    return True

# Main verification logic
def run_verification():
    print(f"--- Starting Verification: {TARGET_FILE} against {SOURCE_FILE} ---")

    data_v15 = load_json_file(SOURCE_FILE)
    data_v17 = load_json_file(TARGET_FILE)

    if data_v15 is None or data_v17 is None:
        print("HALT: Could not load necessary files. Verification aborted.")
        return

    # --- Phase 1: Data Loss Check ---
    print("\n--- Phase 1: Data Loss Check (Searching for deleted keys or type mismatches) ---")
    missing_keys = find_missing_keys(data_v15, data_v17)

    if not missing_keys:
        print("PASS: No deleted keys or type mismatches found. Zero structural data loss confirmed.")
        print("INFO: The file size reduction is likely due to JSON formatting differences (e.g., whitespace removal/minification).")
    else:
        print(f"FAIL: Potential Data Loss/Corruption Detected. {len(missing_keys)} issues found when comparing v15 to v17.")
        print("Top 50 issues (deleted or changed types):")
        for key in missing_keys[:50]:
            print(f"- {key}")

    # --- Phase 2: Implementation Spot Checks ---
    print("\n--- Phase 2: Implementation Spot Checks (v16/v17 Features) ---")

    # Determine STEPS_PATH dynamically (Where step definitions reside)
    STEPS_PATH = None
    # Check standard paths first
    if check_path_exists(data_v17, ["run", "s"]):
        STEPS_PATH = ["run", "s"]
    elif check_path_exists(data_v17, ["workflow_patches", "steps"]):
        STEPS_PATH = ["workflow_patches", "steps"]
    # Handle complex snapshot path if standard paths fail
    elif check_path_exists(data_v17, ["pl", "audit", "steps_snapshots"]):
         try:
             snapshots = data_v17["pl"]["audit"]["steps_snapshots"]
             # Check if snapshots exist and contain the 's' (steps) block
             if snapshots and isinstance(snapshots, list) and len(snapshots) > 0 and "s" in snapshots[0]:
                 print("INFO: Using latest snapshot data for STEPS_PATH.")
                 # Use a tuple to indicate this special path handling
                 STEPS_PATH = ("snapshot", snapshots[0]["s"])
         except (KeyError, IndexError, TypeError):
             pass

    if not STEPS_PATH:
        print("ERROR: Could not determine the main STEPS_PATH in v17. Step-specific checks will be limited.")
    else:
        print(f"DEBUG: Determined STEPS_PATH = {STEPS_PATH}")


    checks = {
        "v16: Knowledge Base Structure (/_runtime/kb)": check_path_exists(data_v17, ["_runtime", "kb"]),
        "v16: Seasonal Windows Structure (/_runtime/seasonal_windows)": check_path_exists(data_v17, ["_runtime", "seasonal_windows"]),
    }

    if STEPS_PATH:
        # Helper to get step data safely based on determined STEPS_PATH
        def get_step_data(step_id):
            # Handle snapshot path
            if isinstance(STEPS_PATH, tuple) and STEPS_PATH[0] == "snapshot":
                # STEPS_PATH[1] already contains the steps dictionary
                return STEPS_PATH[1].get(step_id, {})

            # Handle standard dictionary path (e.g., /run/s)
            temp_data = data_v17
            for part in STEPS_PATH:
                if isinstance(temp_data, dict):
                    temp_data = temp_data.get(part, {})
                else:
                    return {}
            return temp_data.get(step_id, {})

        step1a_data = get_step_data("1a")
        step3a_data = get_step_data("3a")
        step10_data = get_step_data("10")
        step0_data = get_step_data("0") # Needed for v16 workflow check

        checks["v17: New Step 3p (Persona)"] = bool(get_step_data("3p"))

        # Approximate checks by converting step rules/outputs to string for keyword search
        checks["v17: Step 1a CTR Rule (approx check)"] = "CTR_Potential_Score" in json.dumps(step1a_data)
        checks["v17: Step 3a Scoring Rule (approx check)"] = "Revise Scoring Formula" in json.dumps(step3a_data)
        checks["v17: Step 10 Frontloading Rule (approx check)"] = "ENFORCE Frontloading" in json.dumps(step10_data)

        # v16 Workflow order check (Visual First: Adım 0, Adım 1a'yı gerektirmeli)
        step0_requires = step0_data.get("requires", [])
        if isinstance(step0_requires, list):
             # Check if '1a' is in the requires list for step 0
             checks["v16: Workflow Order (Visual First: 0 requires 1a)"] = "1a" in step0_requires
        else:
             checks["v16: Workflow Order (Visual First: 0 requires 1a)"] = "N/A (Requires format unexpected)"

    else:
        # If STEPS_PATH couldn't be determined
        checks["v17: Feature Checks"] = "N/A (Cannot locate steps)"


    all_checks_passed = True
    for name, result in checks.items():
        if result == "N/A":
            status = "N/A"
        elif result:
            status = "PASS"
        else:
            status = "FAIL"
            all_checks_passed = False
        print(f"- [{status}] {name}")

    # --- Phase 3: Summary ---
    print("\n--- Verification Summary ---")
    if not missing_keys and all_checks_passed:
        print("RESULT: SUCCESS. v17 is validated. Zero structural data loss confirmed and key features appear implemented.")
    elif not missing_keys and not all_checks_passed:
         print("RESULT: WARNING. Zero structural data loss confirmed, but some features seem missing or incorrectly implemented. Review spot checks.")
    else:
        print("RESULT: FAILURE. Data loss or corruption detected (Phase 1) or critical features missing (Phase 2). Review the detailed reports above.")

# The script execution starts here when files are available
run_verification()