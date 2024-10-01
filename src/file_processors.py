import os
import json
import xml.etree.ElementTree as ET
import re
import logging
from src.language_utils import get_target_language
from src.translation import batch_translate_texts

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

def process_json(file_path: str, node: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        if node in data:
            texts_to_translate = []
            keys_to_update = []
            
            for key, value in data[node].items():
                if key != "slug" and isinstance(value, str):
                    texts_to_translate.append(value)
                    keys_to_update.append(key)
            
            if texts_to_translate:
                translated_texts = batch_translate_texts(texts_to_translate, target_lang, model)
                for key, translated in zip(keys_to_update, translated_texts):
                    data[node][key] = translated
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
        logging.info(f"Successfully processed JSON: {file_path}")
    except Exception as e:
        logging.error(f"Error processing JSON {file_path}: {e}")
        raise

def process_xml(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        texts_to_translate = []
        elements_to_update = []
        
        for elem in root.iter():
            if elem.text and elem.text.strip():
                texts_to_translate.append(elem.text)
                elements_to_update.append(elem)
        
        if texts_to_translate:
            translated_texts = batch_translate_texts(texts_to_translate, target_lang, model)
            for elem, translated in zip(elements_to_update, translated_texts):
                elem.text = translated
        
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        logging.info(f"Successfully processed XML: {file_path}")
    except Exception as e:
        logging.error(f"Error processing XML {file_path}: {e}")
        raise

def process_xliff(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        texts_to_translate = []
        elements_to_update = []
        
        for trans_unit in root.findall('.//{urn:oasis:names:tc:xliff:document:1.2}trans-unit'):
            source = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}source')
            if source is not None and source.text and source.text.strip():
                texts_to_translate.append(source.text)
                target = trans_unit.find('{urn:oasis:names:tc:xliff:document:1.2}target')
                if target is None:
                    target = ET.SubElement(trans_unit, '{urn:oasis:names:tc:xliff:document:1.2}target')
                elements_to_update.append(target)
        
        if texts_to_translate:
            translated_texts = batch_translate_texts(texts_to_translate, target_lang, model)
            for elem, translated in zip(elements_to_update, translated_texts):
                elem.text = translated
        
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        logging.info(f"Successfully processed XLIFF: {file_path}")
    except Exception as e:
        logging.error(f"Error processing XLIFF {file_path}: {e}")
        raise

def process_markdown(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        translated_content = batch_translate_texts([content], target_lang, model)[0]
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)
        
        logging.info(f"Successfully processed Markdown file: {file_path}")
    except Exception as e:
        logging.error(f"Error processing Markdown file {file_path}: {e}")
        raise

def process_text(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        translated_content = batch_translate_texts([content], target_lang, model)[0]
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)
        
        logging.info(f"Successfully processed text file: {file_path}")
    except Exception as e:
        logging.error(f"Error processing text file {file_path}: {e}")
        raise

def process_file(file_path: str, model: str, default_lang: str):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.json':
        process_json(file_path, 'content', model, default_lang)
    elif ext == '.xml':
        process_xml(file_path, model, default_lang)
    elif ext == '.xlf':
        process_xliff(file_path, model, default_lang)
    elif ext == '.txt':
        process_text(file_path, model, default_lang)
    elif ext in ['.md', '.markdown']:
        process_markdown(file_path, model, default_lang)
    else:
        logging.warning(f"Unsupported file type: {ext}")
