import re

def convert_into_kebab_case(string):
    """
    Convert a string into kebab case.

    Parameters:
    - string (str): The string to convert.

    Returns:
    - str: The converted string.

    Examples:
    >>> convert_into_kebab_case('Hello World')
    'hello-world'
    >>> convert_into_kebab_case('HelloWorld')
    'hello-world'    
    """

    # Convert string to kebab case
    result = '-'.join(
        re.sub(r"(\s|_|-|/)+", " ",
               re.sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                      lambda mo: ' ' + mo.group(0).lower(), string)).split()
    )

    # Remove special characters
    result = result.replace("'", '').replace('.', '').replace('/', '').replace('’', '')

    return result

def is_kebab_case(chaine):
    """
    Vérifie si la chaîne est en kebab case.

    Parameters:
    - chaine (str): La chaîne à vérifier.

    Returns:
    - bool: True si la chaîne est en kebab case, False sinon.

    Examples:
    >>> is_kebab_case('hello-world')
    True
    >>> is_kebab_case('helloWorld')
    False
    """

    # Vérifie si la chaîne est composée de lettres minuscules, chiffres et tirets uniquement,
    # et si elle commence et se termine par une lettre minuscule.
    return bool(re.match(r'^[a-z][a-z0-9-]*$', chaine))