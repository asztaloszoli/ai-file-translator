import os
import re
from language_tags import tags
import logging
import xml.etree.ElementTree as ET

def get_target_language(file_path: str, default_lang: str) -> str:
    """
    Determine the target language from the file name or metadata.
    Returns the ISO 639-1 language code.
    """
    file_name = os.path.basename(file_path)
    
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
    
    # For XLIFF files, try to extract the target language from the file content
    if file_path.lower().endswith('.xlf'):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            target_lang = root.find('.//{urn:oasis:names:tc:xliff:document:1.2}file').get('target-language')
            if target_lang:
                tag = tags.tag(target_lang)
                if tag.valid:
                    return str(tag.language)  # This returns the ISO 639-1 code
        except Exception as e:
            logging.warning(f"Error extracting language from XLIFF: {e}")
    
    # If no language is found, return the default
    return default_lang
