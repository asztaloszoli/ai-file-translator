import os
import json
import xml.etree.ElementTree as ET
import re
import logging
import configparser
from .translation import batch_translate_texts
from .language_utils import get_target_language
from langdetect import detect, LangDetectException

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'text'):  # Ha az objektumnak van text attribútuma
            return obj.text
        return super().default(obj)

def print_safe(text: str):
    """Biztonságos kiírás, ami kezeli a kódolási hibákat"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', 'replace').decode('utf-8'))

# Francia szavak és kifejezések listája a jobb felismeréshez
french_words = [
    # Általános francia szavak
    'de', 'le', 'la', 'les', 'du', 'des', 'un', 'une', 'et', 'ou', 
    'pour', 'dans', 'sur', 'avec', 'sans', 'par', 'en', 'au', 'aux',
    # Játékspecifikus francia szavak
    'Tour', 'Contrôle', 'Avant', 'Poste', 'Service', 'Véhicules',
    'Porte', 'Passage', 'Salle', 'Jour', 'Meilleur', 'Salon',
    'Jump', 'danger', 'Services', 'Pilote', 'Scan', 'Cours',
    'Restez', 'Immobile', 'Comment', 'passe', 'Transport',
    'NE', 'PAS', 'ENTRER', 'Système', 'Recyclage',
    # Új francia szavak
    'Accueil', 'Nous', 'Contacter', 'À', 'Propos', 'Accès', 'Principal',
    'Hangar', 'Cargo', 'mission', 'Disponible', 'Garage',
    'Sauvegarder', 'Annuler', 'Confirmer', 'Champ', 'requis', 'Format',
    'incorrect',
    # További francia szavak a JSON fájlból
    'Minimum', 'caractères', 'Adresse', 'Mon', 'profil', 'Rechercher',
    'Filtres', 'Trop', 'long', 'Continuer', 'Fermer', 'compris',
    'Ignorer', 'Solutions', 'alternatives', 'Progression', 'support',
    'Disponibilité'
]

def is_text_french(text):
    """Ellenőrzi, hogy a szöveg francia-e"""
    try:
        # Konvertáljuk kisbetűssé a szöveget a jobb felismeréshez
        text_lower = text.lower()
        
        # Először próbáljuk meg a nyelvfelismerést
        detected_lang = detect(text_lower)
        if detected_lang == 'fr':
            return True
            
        # Ha nem francia, nézzük meg a francia szavakat
        words = text_lower.split()
        french_word_count = sum(1 for word in words if any(fw.lower() == word for fw in french_words))
        
        # Ha van legalább egy francia szó, vagy tartalmaz speciális francia karaktereket
        return french_word_count > 0 or any(c in text for c in 'éèêëàâäôöûüùïîç')
    except LangDetectException:
        # Ha a nyelvfelismerés nem sikerül, nézzük meg a francia szavakat és karaktereket
        words = text_lower.split()
        french_word_count = sum(1 for word in words if any(fw.lower() == word for fw in french_words))
        return french_word_count > 0 or any(c in text for c in 'éèêëàâäôöûüùïîç')

def count_french_words(text):
    """Megszámolja a francia szavakat a szövegben"""
    words = text.split()
    return sum(1 for word in words if any(fw.lower() in word.lower() for fw in french_words))

def preprocess_text(text):
    """Előfeldolgozza a szöveget a fordítás előtt"""
    # Ha a szöveg egy TextBlock objektum stringje, vegyük ki belőle a szöveget
    if "[TextBlock" in text:
        try:
            text_start = text.find('text=') + 6
            text_end = text.find("', type=") if "', type=" in text else text.find('", type=')
            if text_start > 5 and text_end > text_start:
                text = text[text_start:text_end].strip('"\'')
        except:
            pass
    return text

def process_json(file_path: str, node: str, model: str, default_lang: str):
    print_safe(f"\nProcessing JSON file: {file_path}")
    target_lang = get_target_language(file_path, default_lang)
    print_safe(f"Target language: {target_lang}")
    
    # Ellenőrizzük, hogy van-e mentett állapot
    progress_file = file_path + '.progress'
    translated_keys = set()
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                translated_keys = set(json.load(f))
            print_safe(f"\nFound saved progress: {len(translated_keys)} keys already translated")
        except:
            print_safe("\nCould not load progress file, starting from beginning")
            translated_keys = set()
    
    # Beolvassuk a JSON fájlt
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    texts_to_translate = []
    keys_to_update = []
    
    def process_node(node_data, parent_key=''):
        if isinstance(node_data, dict):
            for key, value in node_data.items():
                current_key = f"{parent_key}.{key}" if parent_key else key
                
                if isinstance(value, (dict, list)):
                    process_node(value, current_key)
                elif isinstance(value, str) and value.strip():
                    try:
                        # Ha már le van fordítva ez a kulcs, kihagyjuk
                        if current_key in translated_keys:
                            print_safe(f"\nSkipping already translated key: {current_key}")
                            continue
                            
                        text_to_check = value.strip()
                        is_french = is_text_french(text_to_check)
                        french_word_count = count_french_words(text_to_check)
                        
                        # Előfeldolgozzuk a szöveget
                        text_to_translate = preprocess_text(text_to_check)
                        
                        # Ha a szöveg francia vagy tartalmaz francia kifejezéseket
                        if is_french or french_word_count >= 1 or text_to_translate != text_to_check:
                            print_safe(f"Found French text: {value}")
                            texts_to_translate.append(text_to_translate)
                            keys_to_update.append((node_data, key, current_key))
                    except LangDetectException:
                        pass
        elif isinstance(node_data, list):
            for i, item in enumerate(node_data):
                current_key = f"{parent_key}[{i}]"
                process_node(item, current_key)
    
    # Ha node meg van adva, csak azt a részfát járjuk be
    if node is not None and node in data:
        print_safe(f"\nProcessing only node: {node}")
        process_node(data[node])
    else:
        print_safe("\nProcessing entire JSON tree")
        process_node(data)
    
    print_safe(f"\nNumber of texts to translate: {len(texts_to_translate)}")
    
    if texts_to_translate:
        print_safe("\nStarting translation...")
        # Batch-ekben fordítjuk a szövegeket
        batch_size = 10
        for i in range(0, len(texts_to_translate), batch_size):
            batch = texts_to_translate[i:i+batch_size]
            batch_keys = keys_to_update[i:i+batch_size]
            
            print_safe(f"\nProcessing batch {i//batch_size + 1}/{(len(texts_to_translate) + batch_size - 1)//batch_size}")
            translated_batch = batch_translate_texts(batch, default_lang, model)
            
            # Frissítjük és azonnal mentjük a változtatásokat
            for (node_data, key, full_key), translated_text in zip(batch_keys, translated_batch):
                print_safe(f"\nUpdating key: {full_key}")
                print_safe(f"Old value: {node_data[key]}")
                print_safe(f"New value: {translated_text}")
                node_data[key] = translated_text
                
                # Hozzáadjuk a lefordított kulcsot a listához
                translated_keys.add(full_key)
                
                # Minden fordítás után mentjük a haladást
                try:
                    print_safe("\nSaving progress...")
                    with open(progress_file, 'w', encoding='utf-8') as f:
                        json.dump(list(translated_keys), f, indent=4)
                except Exception as e:
                    print_safe(f"Error saving progress: {str(e)}")
                
                # Mentjük a JSON fájlt is
                try:
                    print_safe("\nSaving changes to file...")
                    with open(file_path, 'w', encoding='utf-8') as save_file:
                        json.dump(data, save_file, indent=4, ensure_ascii=False, cls=CustomJSONEncoder)
                    print_safe("File saved successfully!")
                except Exception as e:
                    print_safe(f"Error saving file: {str(e)}")
                    return
    
    # Ha minden kész, töröljük a progress fájlt
    if os.path.exists(progress_file):
        try:
            os.remove(progress_file)
            print_safe("\nProgress file removed - translation completed")
        except:
            print_safe("\nCould not remove progress file")

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
            translated_texts = batch_translate_texts(texts_to_translate, default_lang, model)
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
            translated_texts = batch_translate_texts(texts_to_translate, default_lang, model)
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
        
        translated_content = batch_translate_texts([content], default_lang, model)[0]
        
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
        
        translated_content = batch_translate_texts([content], default_lang, model)[0]
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)
        
        logging.info(f"Successfully processed text file: {file_path}")
    except Exception as e:
        logging.error(f"Error processing text file {file_path}: {e}")
        raise

def process_ini(file_path: str, model: str, default_lang: str):
    """
    INI fájl feldolgozása és fordítása
    """
    try:
        print_safe(f"\nProcessing INI file: {file_path}")
        print_safe(f"Target language: {default_lang}\n")

        # Először próbáljuk meg egyszerű kulcs-érték párként olvasni
        lines = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin1') as f:
                lines = f.readlines()

        # Ellenőrizzük, hogy van-e szekció
        has_sections = False
        for line in lines:
            if line.strip().startswith('[') and line.strip().endswith(']'):
                has_sections = True
                break

        texts_to_translate = []
        keys_to_update = []

        if has_sections:
            # Szekciókkal rendelkező INI fájl feldolgozása
            config = configparser.ConfigParser()
            try:
                config.read(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                config.read(file_path, encoding='latin1')

            for section in config.sections():
                print_safe(f"\nChecking section: {section}")
                for key in config[section]:
                    value = config[section][key]
                    print_safe(f"\nChecking key: {key}")

                    # Ha a szöveg nem üres, ellenőrizzük, hogy francia-e
                    if value.strip():
                        try:
                            # Ha a szöveg egy TextBlock objektum stringje, vegyük ki belőle a szöveget
                            text_to_check = value
                            if "[TextBlock" in value:
                                try:
                                    text_start = value.find('text=') + 6
                                    text_end = value.find("', type=") if "', type=" in value else value.find('", type=')
                                    if text_start > 5 and text_end > text_start:
                                        text_to_check = value[text_start:text_end].strip('"\'')
                                except:
                                    pass
                            
                            # Próbáljuk meg feldarabolni a szöveget, ha több nyelv van benne
                            text_parts = re.split(r'([A-Z][A-Z0-9_]+(?:\s*[:-]\s*|\s+))', text_to_check)
                            for part in text_parts:
                                if part.strip():
                                    try:
                                        detected_lang = detect(part)
                                        if detected_lang == 'fr':
                                            print_safe(f"Found French text: {value}")
                                            texts_to_translate.append(value)
                                            keys_to_update.append((section, key))
                                            break  # Ha találtunk francia részt, az egész értéket lefordítjuk
                                    except LangDetectException:
                                        pass
                        except LangDetectException:
                            pass
        else:
            # Egyszerű kulcs-érték párok feldolgozása
            for line in lines:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    if value.strip():
                        try:
                            # Ha a szöveg egy TextBlock objektum stringje, vegyük ki belőle a szöveget
                            text_to_check = value
                            if "[TextBlock" in value:
                                try:
                                    text_start = value.find('text=') + 6
                                    text_end = value.find("', type=") if "', type=" in value else value.find('", type=')
                                    if text_start > 5 and text_end > text_start:
                                        text_to_check = value[text_start:text_end].strip('"\'')
                                except:
                                    pass
                            
                            # Próbáljuk meg feldarabolni a szöveget, ha több nyelv van benne
                            text_parts = re.split(r'([A-Z][A-Z0-9_]+(?:\s*[:-]\s*|\s+))', text_to_check)
                            for part in text_parts:
                                if part.strip():
                                    try:
                                        detected_lang = detect(part)
                                        if detected_lang == 'fr':
                                            print_safe(f"Found French text: {value}")
                                            texts_to_translate.append(value)
                                            keys_to_update.append(key.strip())
                                            break  # Ha találtunk francia részt, az egész értéket lefordítjuk
                                    except LangDetectException:
                                        pass
                        except LangDetectException:
                            pass

        print_safe(f"\nNumber of texts to translate: {len(texts_to_translate)}")

        if texts_to_translate:
            print_safe("\nStarting translation...")
            
            # Szövegek fordítása
            translations = batch_translate_texts(texts_to_translate, default_lang, model)

            # Frissítjük az eredeti fájlt a fordításokkal
            if has_sections:
                # Szekciókkal rendelkező INI fájl frissítése
                for (section, key), translated in zip(keys_to_update, translations):
                    print_safe(f"\nUpdating section: {section}, key: {key}")
                    print_safe(f"Old value: {config[section][key]}")
                    print_safe(f"New value: {translated}")
                    config[section][key] = translated

                # Visszaírjuk a fájlba
                print_safe("\nWriting back to file...")
                with open(file_path, 'w', encoding='utf-8') as file:
                    config.write(file)
            else:
                # Egyszerű kulcs-érték párok frissítése
                updated_lines = []
                line_idx = 0
                trans_idx = 0
                
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        if key in keys_to_update:
                            # Ez egy lefordítandó sor
                            translated = translations[trans_idx]
                            updated_lines.append(f"{key}={translated}\n")
                            trans_idx += 1
                        else:
                            # Ez egy változatlan sor
                            updated_lines.append(line + '\n')
                    else:
                        # Üres sor vagy komment
                        updated_lines.append(line + '\n')
                        
                # Visszaírjuk a fájlba
                print_safe("\nWriting back to file...")
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(updated_lines)
                    
            print_safe("File updated successfully")

    except Exception as e:
        print_safe(f"\nError processing INI {file_path}: {str(e)}")
        raise

def process_file(file_path: str, model: str, default_lang: str):
    print(f"Processing file: {file_path}")  # Debug print
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.json':
        process_json(file_path, None, model, default_lang)  # A None azt jelzi, hogy nincs szükség node-ra
    elif ext == '.xml':
        process_xml(file_path, model, default_lang)
    elif ext == '.xlf':
        process_xliff(file_path, model, default_lang)
    elif ext == '.txt':
        process_text(file_path, model, default_lang)
    elif ext in ['.md', '.markdown']:
        process_markdown(file_path, model, default_lang)
    elif ext == '.ini':
        process_ini(file_path, model, default_lang)
    else:
        logging.warning(f"Unsupported file type: {ext}")
