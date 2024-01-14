def sort_dict_by_alphabetical_order_for_specific_key(dict, key):
    """
    Sort a dict by keys

    Parameters:
    - dict (dict): The dictionary to sort.
    - key (str): The key to sort by.

    Returns:
    - dict: The sorted dictionary.
    """

    sorted_data = sorted(dict, key=lambda item: item[key])
    
    return sorted_data

# def sort_keys(dict, keys):
#     """Sort a dict by keys"""

#     sorted_data = sorted(dict.keys())
    
#     return sorted_data

def check_if_string_exists_in_dict_for_specific_key(searched_string, key, data):
    """
    Check if a string exists in a nested dictionary.

    Parameters:
    - searched_string (str): The string to search for.
    - key (str): The key to check within the nested dictionaries.
    - data (dict): The nested dictionary to search within.

    Returns:
    - bool: True if the string is found, False otherwise.
    """

    for item in data.values():
        if isinstance(item, dict):
            if key in item and item[key] == searched_string:
                return True
            elif check_if_string_exists_in_dict_for_specific_key(searched_string, key, item):
                return True
    return False

def check_if_string_exists_in_dict(searched_string, data):
    """
    Check if a string exists in a nested dictionary.

    Parameters:
    - searched_string (str): The string to search for.
    - data (dict): The nested dictionary to search within.

    Returns:
    - bool: True if the string is found, False otherwise.
    """

    for item in data.values():
        if isinstance(item, dict):
            if any(isinstance(value, str) and searched_string in value for value in item.values()):
                return True
            elif check_if_string_exists_in_dict(searched_string, item):
                return True
    return False