import json

# Define the input and output file paths
input_filename = 'final_json__ADDONLY_runtime_ref_gate__20250923T064102Z__alias_fix_8a_only.json'
output_filename = 'cekirdek_kurallar.json'

# Keys to remove from the top level
keys_to_remove = [
    '_artifacts',
    '_audit',
    '_receipts',
    '_run',
    'similar_keywords',
    'top_listings',
    'patch_log',
    'changes'
]

# Read the original JSON file
try:
    with open(input_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: Input file '{input_filename}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from '{input_filename}'.")
    exit(1)

# Remove the specified top-level keys
for key in keys_to_remove:
    if key in data:
        del data[key]

# Remove the nested '/token_tracking/changes' key
if '_meta' in data and 'token_tracking' in data['_meta'] and 'changes' in data['_meta']['token_tracking']:
    del data['_meta']['token_tracking']['changes']
# The path in the user request was /token_tracking/changes, which might be a top-level key.
# Let's check for that as well.
if 'token_tracking' in data and 'changes' in data['token_tracking']:
    del data['token_tracking']['changes']


# Write the cleaned data to the new file
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Successfully created '{output_filename}' by cleaning '{input_filename}'.")
