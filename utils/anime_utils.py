import re
from utils.replaces import mapping, mappingrev, searchmap

def clean_text(text):
    """Clean and normalize text by removing extra spaces and fixing encoding issues"""
    if not text:
        return None
    text = re.sub(r'&#\d+;', lambda m: chr(int(m.group(0)[2:-1])) if m.group(0)[2:-1].isdigit() else m.group(0), text)
    text = text.replace('\\', '').replace('\n', ' ').strip()
    return ' '.join(text.split())

def replace_tit(title, mapping):
    for original_text, replacement_text in mapping.items():
        title = title.replace(original_text, replacement_text)
    return title

def replace_tit_rev(title, mappingrev):
    for original_text, replacement_text in mappingrev.items():
        title = title.replace(original_text, replacement_text)
    return title

def replace_search(title, searchmap):
    for original_text, replacement_text in searchmap.items():
        title = re.sub(re.escape(original_text), replacement_text, title, flags=re.IGNORECASE)
    return title

def convert_title(input_string):
    input_string = replace_tit_rev(input_string, mappingrev)
    input_string = input_string.replace("_"," ").replace("ies", ":").replace(" TV", " (TV)").replace("xb", ".").replace("dsj", ",")
    # ... rest of the conversion logic
    parts = input_string.split("=")
    return parts[1] if len(parts) > 1 else input_string

def convert_dl_title(input_string):
    input_string = replace_tit_rev(input_string, mappingrev)
    input_string = input_string.replace("_"," ").replace("ies", ":").replace(" TV", " (TV)").replace("xb", ".").replace("dsj", ",")
    # ... rest of the conversion logic
    parts = input_string.split("=")
    return f"{parts[1]} {parts[2]}" if len(parts) > 1 else input_string
