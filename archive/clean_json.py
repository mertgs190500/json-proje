import json
import collections.abc

def remove_keys_recursive(obj, keys_to_remove):
    """
    Recursively remove specified keys from a dictionary or a list of dictionaries.
    """
    if isinstance(obj, dict):
        # Create a new dictionary excluding the keys to remove
        return {key: remove_keys_recursive(value, keys_to_remove) for key, value in obj.items() if key not in keys_to_remove}
    elif isinstance(obj, list):
        # Recursively process each item in the list
        return [remove_keys_recursive(item, keys_to_remove) for item in obj]
    else:
        # Return the object as is if it's not a dict or list
        return obj

def main():
    input_filename = 'cekirdek_kurallar.json'
    output_filename = 'uretim_cekirdek.json'

    # Keys to remove from the entire JSON structure
    keys_to_remove = {'description', 'notes', 'title', 'label', 'examples', 'example_header', 'example_rows'}

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Remove specified keys recursively
        cleaned_data = remove_keys_recursive(data, keys_to_remove)

        # Save the new optimized version
        with open(output_filename, 'w', encoding='utf-8') as f:
            # Use separators=(',', ':') for minified output
            json.dump(cleaned_data, f, ensure_ascii=False, separators=(',', ':'))

        print(f"Successfully created optimized file: {output_filename}")

    except FileNotFoundError:
        print(f"Error: The file {input_filename} was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {input_filename}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
