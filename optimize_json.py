import json
import hashlib
import collections

# Adım 2: Anahtar Kısaltma Haritası
KEY_MAP = {
    "__manifest": "m", "_final_safety": "fs", "source_of_truth": "sot", "description": "d",
    "constraints": "c", "execution_order": "eo", "__backups": "bk", "__policy__": "p",
    "__rules__": "r", "_admin": "adm", "_bootstrap": "bs", "_commands": "cmd",
    "_csv_rules": "csv", "_export_contract": "exp", "_help": "h", "_meta": "mt",
    "_padding": "pad", "_policy": "pl", "_product_static": "ps", "_profiles": "prof",
    "_run_order": "run", "_self_guard": "sg", "_store_profile": "sp", "_workflow_patches": "wp",
    "features": "f", "policy_version": "pv", "artifact_versioning": "av", "deterministic_seed": "seed",
    "forbid_field_overwrite": "f_f_ow", "forbid_silent_drop": "f_s_d", "no_merge_by_default": "no_m_d",
    "require_changelog_for_any_edit": "req_chg", "default_no_skip": "d_no_s",
    "default_requires_policy": "d_req_p", "no_step_skip": "no_s_s", "result_only_mode_mandatory": "res_only",
    "stop_on_preprocessing_error": "stop_err", "strict_order": "strict_o", "unlock_request": "unlock",
    "approved_at": "app_at", "rationale": "rat", "requested_steps": "req_steps", "on_load": "on_l",
    "banner_text": "b_txt", "session_banner": "s_ban", "allowed": "allow", "descriptions": "ds",
    "headers": "hdrs", "preprocess": "pre", "outputs": "o", "required": "req", "validations": "v",
    "columns": "cols", "created_at": "cr_at", "diff_journal": "diff_j", "runtime_persistence": "rt_p",
    "schema_validation": "schema_v", "sha256_lock": "lock", "versioning": "ver",
    "write_mode": "w_mode", "require_user_approval": "req_ua", "changelog": "chg",
    "dependency_model": "dep_m", "first_message_template": "msg1_tmpl", "last_patched_at": "l_patch_at",
    "auto_continue": "auto_c", "await_user": "await_u", "requires_context": "req_ctx",
    "validators": "vlds", "enabled": "en", "purpose": "purp", "inputs": "i", "checklist": "chk",
    "what_gpt_does": "gpt_do", "what_user_does": "usr_do", "mapping": "map", "product_info": "p_info",
    "fixed_product": "p_fix", "logistics": "logi", "artifacts": "art", "shop_profile": "s_prof",
    "market": "mkt", "language": "lang", "currency": "curr", "units": "u",
    "authoritative_manifest_ref": "auth_ref", "ruleset": "rs", "gates": "g", "flow": "fl",
    "preconditions": "precon", "hitl_contract": "hitl", "upstream_signature": "up_sig",
    "on_change": "on_chg", "depends_on": "dep_on", "on_fail": "on_f", "on_success_next": "on_s_next",
    "on_contract_violation": "on_v_c", "on_miss": "on_m", "on_missing_required_path": "on_m_p",
    "on_soft_misalignment": "on_s_m", "on_validation_fail": "on_v_f", "critical_pass": "c_pass",
    "require_ancestors_done": "req_anc", "parent_defined": "p_def", "step0_review_confirmed": "s0_conf",
    "workflow_enforcement": "wfe", "steps": "s", "governance": "gov", "title": "t", "name": "n",
    "id": "id", "rules": "rls", "params": "prm", "policy": "pol", "message": "msg",
    "severity": "sev", "when": "wh", "type": "typ", "value": "val", "path": "pth", "paths": "pths"
}

def get_obj_hash(obj):
    """Nesneler için deterministik bir hash oluşturur."""
    return hashlib.sha1(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:8]

def find_duplicates(data):
    """JSON verisi içinde tekrar eden nesneleri bulur."""
    if not isinstance(data, (dict, list)):
        return {}

    queue = collections.deque([data])
    hashes = collections.defaultdict(list)
    paths = collections.deque([[]])
    visited_ids = set()

    while queue:
        current_obj = queue.popleft()
        current_path = paths.popleft()

        if id(current_obj) in visited_ids:
            continue
        visited_ids.add(id(current_obj))

        obj_str = json.dumps(current_obj, sort_keys=True)
        if isinstance(current_obj, (dict, list)) and len(obj_str) > 50:
            obj_hash = get_obj_hash(current_obj)
            hashes[obj_hash].append((current_path, current_obj))

        if isinstance(current_obj, dict):
            for key, value in current_obj.items():
                if isinstance(value, (dict, list)):
                    queue.append(value)
                    paths.append(current_path + [key])
        elif isinstance(current_obj, list):
            for i, value in enumerate(current_obj):
                if isinstance(value, (dict, list)):
                    queue.append(value)
                    paths.append(current_path + [i])

    return {h: v for h, v in hashes.items() if len(v) > 1}

def normalize_structure(data):
    """Adım 1: Yapıyı normalize eder. En derin yollardan başlayarak."""
    duplicates = find_duplicates(data)
    if not duplicates:
        return data

    if "_defs" not in data:
        data["_defs"] = {}

    defs = data["_defs"]

    replacements = []
    for obj_hash, items in duplicates.items():
        def_id = f"def_{obj_hash}"
        if def_id not in defs:
            defs[def_id] = items[0][1]

        for path, _ in items:
            replacements.append({'path': path, 'ref': {"$ref": f"#/_defs/{def_id}"}})

    replacements.sort(key=lambda r: len(r['path']), reverse=True)

    for rep in replacements:
        path = rep['path']
        ref = rep['ref']

        try:
            temp = data
            for key in path[:-1]:
                temp = temp[key]
            temp[path[-1]] = ref
        except (KeyError, TypeError, IndexError):
            continue

    return data

def shorten_keys(data):
    """Adım 2: Anahtar isimlerini kısaltır."""
    if isinstance(data, dict):
        return {KEY_MAP.get(k, k): shorten_keys(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [shorten_keys(elem) for elem in data]
    else:
        return data

def main():
    input_filename = 'final.json'
    output_filename = 'uretim_cekirdek_v2.json'

    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Adım 1: Yapıyı Normalize Et
    data = normalize_structure(data)

    # Adım 2: Anahtar İsimlerini Kısalt
    shortened_data = shorten_keys(data)

    # Adım 3: Minify Et ve Dosyaya Yaz
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(shortened_data, f, separators=(',', ':'), ensure_ascii=False)

    print(f"Optimizasyon tamamlandı. Sonuç '{output_filename}' dosyasına yazıldı.")

if __name__ == '__main__':
    main()