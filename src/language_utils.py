import os
import re
import json
import xml.etree.ElementTree as ET
from language_tags import tags
import logging

def get_target_language(file_path: str, default_lang: str) -> str:
    """
    Determine the target language from the file name or metadata.
    Returns the ISO 639-1 language code.
    """
    file_name = os.path.basename(file_path)
    
    # Check filename for language code
    match = re.search(r'[_-]([a-zA-Z]{2,3})(?:\.[^.]+)?$', file_name)
    if match:
        lang_code = match.group(1).lower()
        if lang_code == 'fra':
            return 'fr'
        tag = tags.tag(lang_code)
        if tag.valid:
            return str(tag.language)
        else:
            logging.warning(f"Invalid language code in filename: {lang_code}")
    
    # Check file content for language information
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.json':
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            if 'target-language' in data:
                lang_code = data['target-language']
                tag = tags.tag(lang_code)
                if tag.valid:
                    return str(tag.language)
        except Exception as e:
            logging.warning(f"Error extracting language from JSON: {e}")

    elif ext in ['.xml', '.xlf']:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # For XLIFF files
            if ext == '.xlf':
                target_lang = root.find('.//{urn:oasis:names:tc:xliff:document:1.2}file').get('target-language')
            # For XML files
            else:
                target_lang = root.get('target-language')  # Assuming target-language is an attribute of the root element
            
            if target_lang:
                tag = tags.tag(target_lang)
                if tag.valid:
                    return str(tag.language)
        except Exception as e:
            logging.warning(f"Error extracting language from XML/XLIFF: {e}")
    
    # If no language is found, return the default
    return default_lang
