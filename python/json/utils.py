import json

#tag::sort_json_file_by_alphabetical_order[]
def sort_json_file_by_alphabetical_order(input_file_path, output_file_path, key):
    """Sort a json file by keys"""

    with open(input_file_path, 'r') as f:
        data = json.load(f)

    sorted_data = sorted(data, key=lambda item: item[key])
    
    with open(output_file_path, 'w') as f:
        json.dump(sorted_data, f, indent=4, sort_keys=True)
#end::sort_json_file_by_alphabetical_order[]
        
#tag::delete_duplicate_according_one_key[]
def delete_duplicate_according_one_key(input_file_path, output_file_path, key):
    """Delete duplicate according one key"""

    with open(input_file_path, 'r') as f:
        data = json.load(f)

    unique_values = set()
    output_data = []

    for entry in data:
        key_value = entry.get(key)  # Replace 'key' with the actual key name
        if key_value not in unique_values:
            unique_values.add(key_value)
            output_data.append(entry)

    with open(output_file_path, 'w') as f:
        json.dump(output_data, f, indent=4, sort_keys=True)
#end::delete_duplicate_according_one_key[]
        
#tag::delete_duplicate_according_all_keys[]
def delete_duplicate_according_all_keys(input_file_path, output_file_path):
    """Delete duplicate according all keys"""

    with open(input_file_path, 'r') as f:
        data = json.load(f)

    # Remove duplicate
    data = [i for n, i in enumerate(data) if i not in data[n + 1:]]

    with open(output_file_path, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)