import json
from copy import deepcopy
import hashlib

def set_path(data, path, value):
    """
    Sets a value in a nested dictionary using a path string like '/a/b/c'.
    Creates intermediate dictionaries if they don't exist.
    """
    keys = path.strip('/').split('/')
    current = data
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value

def get_path(data, path, default=None):
    """
    Gets a value from a nested dictionary using a path string.
    Returns default if the path is not found.
    """
    keys = path.strip('/').split('/')
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def rename_key_recursive(data, old_key, new_key):
    """
    Recursively finds and renames a key in a nested data structure.
    """
    if isinstance(data, dict):
        if old_key in data:
            data[new_key] = data.pop(old_key)
        for key, value in data.items():
            rename_key_recursive(value, old_key, new_key)
    elif isinstance(data, list):
        for item in data:
            rename_key_recursive(item, old_key, new_key)

def comprehensive_revision(input_path, output_path):
    """
    Applies a comprehensive set of revisions and performs verification and sealing.
    """
    print(f"Reading data from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # --- BÖLÜM A: TEKNİK UYGULAMA ADIMLARI ---
    print("\n--- Starting Section A: Technical Implementation ---")

    # A.1. Politika Çelişkisi Çözümü
    print("A.1. Updating policy conflict resolution...")
    set_path(data, '/pl/workflow/guards/checklist_enforcer/mode', 'report_and_wait')
    set_path(data, '/workflow_patches/steps_defaults/gates/on_soft_misalignment', 'report_and_wait')

    # A.2. Operasyonel Güvenlik Politikalarının Optimizasyonu
    print("A.2. Optimizing operational security policies...")
    set_path(data, '/pl/security/size_shrink_guard/threshold_bytes', 4096)
    set_path(data, '/pl/security/size_shrink_guard/threshold_percent', 0.005)
    set_path(data, '/pl/workflow/guards/restore_on_every_write/en', False)
    set_path(data, '/pl/workflow/guards/batch_enforcer/max_updates', 50)

    # A.3. Terminoloji ve Kimlik Güncellemesi
    print("A.3. Updating terminology and identity (GPT -> Gemini)...")
    if 'prof' in data and 'gpt_prod_executor_v1' in data['prof']:
        data['prof']['gemini_prod_executor_v1'] = data['prof'].pop('gpt_prod_executor_v1')

    set_path(data, '/pl/handshake/require_actor', 'gemini_prod_executor_v1')

    actor_list = get_path(data, '/wp/guards/actor_check/allow')
    if isinstance(actor_list, list) and 'gpt_prod_executor_v1' in actor_list:
        actor_list[actor_list.index('gpt_prod_executor_v1')] = 'gemini_prod_executor_v1'

    rename_key_recursive(get_path(data, '/h/s'), 'gpt_do', 'gemini_do')
    rename_key_recursive(get_path(data, '/_run/s'), 'gpt_do', 'gemini_do')

    # A.4. Optimizasyon: Token Tasarrufu
    print("A.4. Deleting /pad key...")
    if 'pad' in data:
        del data['pad']

    # A.5. İş Akışı Senkronizasyonu
    print("A.5. Synchronizing workflow execution order...")
    master_order = ['0a', '00', '0', '1', '1a', '1b', '3', '3a', '3b', '3c', '5', '5a', '5c', '6', '6a', '6b', '7', '8', '8a', '8B', '8C', '9', '10', '11', '12', '12a', '13', '14', '15', '16', '17', '18', '19', '20', 'seo_package']

    all_steps = get_path(data, '/workflow_patches/steps')
    new_snapshot = []
    if all_steps:
        for step_id in master_order:
            step_details = all_steps.get(step_id, {})
            new_snapshot.append({
                "id": step_id,
                "ref": f"/workflow_patches/steps/{step_id}",
                "n": step_details.get("n", step_id)
            })

    set_path(data, '/_run_order/steps_list_snapshot', new_snapshot)
    set_path(data, '/step_flow_lock/canonical_order', master_order)
    set_path(data, '/workflow_enforcement/execution_order_all', [{"id": i, "en": True} for i in master_order])

    print("--- Section A completed. ---")

    # --- BÖLÜM B: DOĞRULAMA PROTOKOLÜ VE MÜHÜRLEME ---
    print("\n--- Starting Section B: Verification and Sealing Protocol ---")

    data_for_hashing = deepcopy(data)

    paths_to_clear = [
        '/fs/lock', '/sg/expected_sha256', '/final_marker/sha256',
        '/integrity/byte_size', '/integrity/char_count', '/integrity/content_hash'
    ]
    for path in paths_to_clear:
        keys = path.strip('/').split('/')
        parent = get_path(data_for_hashing, '/'.join(keys[:-1]))
        if isinstance(parent, dict) and keys[-1] in parent:
            parent[keys[-1]] = None

    minified_string = json.dumps(data_for_hashing, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    minified_bytes = minified_string.encode('utf-8')

    new_hash = hashlib.sha256(minified_bytes).hexdigest()
    new_byte_size = len(minified_bytes)
    new_char_count = len(minified_string)

    print(f"  - New SHA256: {new_hash}")
    print(f"  - New byte_size: {new_byte_size}")
    print(f"  - New char_count: {new_char_count}")

    print("B.4. Sealing file with new hash and stats...")
    set_path(data, '/fs/lock', new_hash)
    set_path(data, '/sg/expected_sha256', new_hash)
    set_path(data, '/final_marker/sha256', new_hash)
    set_path(data, '/integrity/byte_size', new_byte_size)
    set_path(data, '/integrity/char_count', new_char_count)
    set_path(data, '/integrity/content_hash', f"sha256:{new_hash}")

    print("--- Section B completed. ---")

    # Final Save
    print(f"\nSaving final revised file to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print("Process completed successfully.")

if __name__ == "__main__":
    INPUT_FILE = "uretim_cekirdek_v2.json"
    OUTPUT_FILE = "uretim_cekirdek_v13_revised.json"
    comprehensive_revision(INPUT_FILE, OUTPUT_FILE)