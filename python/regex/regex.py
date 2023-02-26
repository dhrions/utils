import re

string_pattern = r"[A-Za-zÀ-ÿŒœ@]"
ip_address_pattern = r"((\b25[0-5]|\b2[0-4][0-9]|\b1)?[1-9]?[0-9])(\.((25[0-5]|2[0-4][0-9]|1)?[1-9]?[0-9])){2}(\.((25[0-5]|2[0-4][0-9]|1)?[1-9]?[0-9]))\b"
phonenumber_pattern = r"06(\s\d{2}){4}|06(\d{2}){4}|06(\.\d{2}){4}|06(\-\d{2}){4}"
url_fr_pattern = r"\bw{3}\.\w*\.fr\b"
mac_address_pattern = "([0-9a-f]{2}:){5}[0-9a-f]{2}"

string = "J'aime les chats et les chiens."

matches = re.findall(pattern, string)

for match in matches:
    print(match)
