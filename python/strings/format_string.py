import re

def convert_into_kebab_case(string):
    return '-'.join(
        re.sub(r"(\s|_|-|/)+", " ",
               re.sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
                      lambda mo: ' ' + mo.group(0).lower(), string)).split()
    ).replace("'", '').replace('.', '').replace('/', '').replace('’', '')

def is_kebab_case(chaine):
    # Vérifie si la chaîne est composée de lettres minuscules, chiffres et tirets uniquement,
    # et si elle commence et se termine par une lettre minuscule.
    return bool(re.match(r'^[a-z][a-z0-9-]*$', chaine))
