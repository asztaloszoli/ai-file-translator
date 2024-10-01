import os
import json
import xml.etree.ElementTree as ET
import re
import anthropic
import argparse
import logging
from typing import List, Dict, Any
from datetime import datetime
from language_tags import tags

# Set up logging
def setup_logging(log_dir: str, timestamp: str):
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"translation_log_{timestamp}.log")
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler for relevant info
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_file

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

def get_target_language(file_path: str, default_lang: str) -> str:
    """
    Determine the target language from the file name or metadata.
    Returns the ISO 639-1 language code.
    """
    file_name = os.path.basename(file_path)
    
    # Check for language code in file name (e.g., "filename_es.json" or "filename-es.json")
    match = re.search(r'[_-]([a-zA-Z]{2,3})(?:\.[^.]+)?$', file_name)
    if match:
        lang_code = match.group(1).lower()
        tag = tags.tag(lang_code)
        if tag.valid:
            return str(tag.language)  # This returns the ISO 639-1 code
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

def batch_translate_texts(texts: List[str], target_lang: str, model: str) -> List[str]:
    client = anthropic.Anthropic()
    try:
        content = "\n\n".join([f"Text {i+1}: {text}" for i, text in enumerate(texts)])
        
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=0,
            system=f"You are a translator. Translate the following texts to {target_lang}. Maintain the original structure and numbering in your response, but keep the 'Text N:' labels in English.",
            messages=[
                {"role": "user", "content": content}
            ]
        )
        
        response_content = message.content
        logging.debug(f"Raw response content: {response_content}")
        
        if isinstance(response_content, list) and len(response_content) > 0:
            text_block = response_content[0]
            if hasattr(text_block, 'text'):
                response_text = text_block.text
            else:
                response_text = str(text_block)
        else:
            response_text = str(response_content)
        
        logging.debug(f"Processed response text: {response_text[:100]}...")
        
        translated_texts = []
        for i, text in enumerate(texts):
            start_marker = f"Text {i+1}: "
            end_marker = f"\n\nText {i+2}: " if i < len(texts) - 1 else ""
            start_index = response_text.find(start_marker)
            if start_index != -1:
                end_index = response_text.find(end_marker, start_index) if end_marker else len(response_text)
                translated_text = response_text[start_index + len(start_marker):end_index].strip()
                translated_texts.append(translated_text)
            else:
                # Fallback: try to find "Texto N:" if "Text N:" is not found
                fallback_start_marker = f"Texto {i+1}: "
                fallback_end_marker = f"\n\nTexto {i+2}: " if i < len(texts) - 1 else ""
                fallback_start_index = response_text.find(fallback_start_marker)
                if fallback_start_index != -1:
                    fallback_end_index = response_text.find(fallback_end_marker, fallback_start_index) if fallback_end_marker else len(response_text)
                    translated_text = response_text[fallback_start_index + len(fallback_start_marker):fallback_end_index].strip()
                    translated_texts.append(translated_text)
                else:
                    logging.warning(f"Could not find marker for Text {i+1}, using original text")
                    translated_texts.append(text)
        
        return translated_texts
    except Exception as e:
        logging.error(f"Translation error: {e}")
        logging.exception("Exception details:")
        return texts

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
                for key, original, translated in zip(keys_to_update, texts_to_translate, translated_texts):
                    data[node][key] = translated
                    logging.info(f"Original: {original[:100]}...")
                    logging.info(f"Translated: {translated[:100]}...")
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
        logging.info(f"Successfully processed JSON: {file_path}")
    except Exception as e:
        logging.error(f"Error processing JSON {file_path}: {e}")

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

def process_xliff(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        texts_to_translate = []
        elements_to_update = []
        
        for elem in root.iter('{urn:oasis:names:tc:xliff:document:1.2}source'):
            if elem.text and elem.text.strip():
                texts_to_translate.append(elem.text)
                elements_to_update.append(elem.find('../{urn:oasis:names:tc:xliff:document:1.2}target'))
        
        if texts_to_translate:
            translated_texts = batch_translate_texts(texts_to_translate, target_lang, model)
            for elem, translated in zip(elements_to_update, translated_texts):
                elem.text = translated
        
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        logging.info(f"Successfully processed XLIFF: {file_path}")
    except Exception as e:
        logging.error(f"Error processing XLIFF {file_path}: {e}")

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

def process_markdown(file_path: str, model: str, default_lang: str):
    target_lang = get_target_language(file_path, default_lang)
    logging.info(f"Detected language for {file_path}: {target_lang}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        parts = re.split(r'(```[\s\S]*?```|\[.*?\]\(.*?\))', content)
        
        translatable_parts = [part for part in parts if not part.startswith('```') and not re.match(r'$$.*?$$$.*?$', part)]
        translated_parts = batch_translate_texts(translatable_parts, target_lang, model)
        
        for i, part in enumerate(parts):
            if part in translatable_parts:
                parts[i] = translated_parts[translatable_parts.index(part)]
        
        translated_content = ''.join(parts)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)
        
        logging.info(f"Successfully processed Markdown file: {file_path}")
    except Exception as e:
        logging.error(f"Error processing Markdown file {file_path}: {e}")

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

def main():
    parser = argparse.ArgumentParser(
        description="Translate files using Anthropic's Claude AI model.",
        epilog="Example: python main.py --path /path/to/files --model claude-3-haiku-20240307 --default-lang en"
    )
    parser.add_argument("--path", default=os.getcwd(), help="Path to directory containing files to translate (default: current directory)")
    parser.add_argument("--model", default="claude-3-haiku-20240307", help="Anthropic model to use for translation (default: claude-3-haiku-20240307)")
    parser.add_argument("--default-lang", default="en", help="Default target language if not specified in filename (default: en)")
    args = parser.parse_args()

    # Set up logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    log_file = setup_logging(log_dir, timestamp)

    logging.info(f"Starting translation process for files in {args.path}")
    logging.info(f"Detailed logs will be written to {log_file}")

    for root, _, files in os.walk(args.path):
        for filename in files:
            file_path = os.path.join(root, filename)
            logging.info(f"Processing file: {file_path}")
            process_file(file_path, args.model, args.default_lang)

    logging.info("Translation process completed")

if __name__ == "__main__":
    main()
