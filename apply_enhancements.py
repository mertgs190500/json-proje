import json
import sys
import collections.abc

def deep_update(d, u):
    """
    Recursively update a dictionary.
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def get_parent_and_key(doc, path):
    """
    Given a JSON path, returns the parent element and the final key.
    This version assumes a dictionary-based traversal using setdefault.
    """
    if not path.startswith('/'):
        raise ValueError(f"JSON path must start with '/': {path}")

    parts = path.strip('/').split('/')
    if not parts or parts == ['']:
        return None, None

    parent = doc
    # Traverse to the parent element, creating nested dicts if they don't exist
    for part_str in parts[:-1]:
        if isinstance(parent, dict):
            parent = parent.setdefault(part_str, {})
        else:
            # This script is not designed to handle creating new list elements during traversal
            raise TypeError(f"Path traverses a non-dict element at '{part_str}' in path '{path}'")

    final_key = parts[-1]
    return parent, final_key

def apply_operation(doc, operation):
    """
    Applies a single operation from the instructions file to the document.
    """
    action_type = operation['action']
    path = operation['path']
    value = operation.get('value')

    parent, key = get_parent_and_key(doc, path)
    if parent is None:
        print(f"  - SKIPPING: Cannot get parent for path '{path}'")
        return

    if not isinstance(parent, dict):
         print(f"  - ERROR: Parent for path '{path}' is not a dictionary. Cannot apply operation.", file=sys.stderr)
         return

    if action_type == 'add_or_merge':
        existing_value = parent.get(key, {})
        if isinstance(existing_value, collections.abc.Mapping) and isinstance(value, collections.abc.Mapping):
            deep_update(existing_value, value)
            parent[key] = existing_value
        else:
            parent[key] = value

    elif action_type == 'update_value':
        parent[key] = value

    elif action_type == 'add_if_not_exists':
        if key not in parent:
            parent[key] = value

    elif action_type == 'append_to_list':
        target_list = parent.setdefault(key, [])
        if not isinstance(target_list, list):
            print(f"  - ERROR: Target for append is not a list at path '{path}'", file=sys.stderr)
            return
        if value not in target_list: # Avoid adding duplicates
            target_list.append(value)

    else:
        print(f"  - WARNING: Unknown action type '{action_type}'")

def main():
    base_file = 'uretim_cekirdek_v13_enhanced.json'
    instructions_file = 'v14_instructions.json'

    try:
        with open(base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load base file '{base_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(instructions_file, 'r', encoding='utf-8') as f:
            instructions = json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load instructions file '{instructions_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Starting enhancement from '{instructions['target_version']}' to '{instructions['new_version']}'.")

    for op_group in instructions['operations']:
        print(f"\nProcessing Group: {op_group['group']}")
        for action in op_group['actions']:
            try:
                apply_operation(data, action)
                print(f"  - Applied action '{action['action']}' to path '{action['path']}'")
            except Exception as e:
                print(f"  - FAILED to apply action for path '{action['path']}'. Error: {e}", file=sys.stderr)

    output_file = f"uretim_cekirdek_{instructions['new_version']}.json"

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        print(f"\nSuccessfully created new strategic configuration file: {output_file}")
    except Exception as e:
        print(f"FATAL: Could not write output file '{output_file}'. Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()