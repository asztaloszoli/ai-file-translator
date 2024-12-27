import json
import re

def fix_encoding(text):
    # Javítjuk a speciális karaktereket
    replacements = {
        # Francia ékezetes karakterek
        'È': 'E',
        'É': 'E',
        'Ê': 'E',
        'Ë': 'E',
        'À': 'A',
        'Â': 'A',
        'Î': 'I',
        'Ï': 'I',
        'Ô': 'O',
        'Û': 'U',
        'Ù': 'U',
        'Ü': 'U',
        'Ÿ': 'Y',
        'Ç': 'C',
        'Œ': 'OE',
        'Æ': 'AE',
        
        # Magyar ékezetes karakterek megtartása
        'á': 'á',
        'é': 'é',
        'í': 'í',
        'ó': 'ó',
        'ö': 'ö',
        'ő': 'ő',
        'ú': 'ú',
        'ü': 'ü',
        'ű': 'ű',
        'Á': 'Á',
        'É': 'É',
        'Í': 'Í',
        'Ó': 'Ó',
        'Ö': 'Ö',
        'Ő': 'Ő',
        'Ú': 'Ú',
        'Ü': 'Ü',
        'Ű': 'Ű'
    }
    
    # Először a francia ékezetes karaktereket javítjuk
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Speciális kifejezések kezelése
    text = re.sub(r'WIP\s*-\s*', 'WIP - ', text)  # WIP után egységes szóköz
    text = text.replace('Ellenőrző', 'Ellenőrző')  # Javítjuk az "éllenőrző" hibát
    text = text.replace('Előőrs', 'Előőrs')  # Javítjuk az "élőőrs" hibát
    text = text.replace('Elhagyott', 'Elhagyott')  # Javítjuk az "élhagyott" hibát
    
    return text

def fix_line_endings(text):
    # Először eltávolítjuk a felesleges sortöréseket
    text = text.replace('\\n\\n', '\\n')
    
    # Ha a sor végén van \n, eltávolítjuk
    text = text.rstrip('\\n')
    
    # A megmaradt \n karaktereket valódi sortörésre cseréljük
    if '\\n' in text:
        parts = text.split('\\n')
        # Eltávolítjuk az üres részeket
        parts = [p.strip() for p in parts if p.strip()]
        text = '\n'.join(parts)
    
    return text

def json_to_ini(json_file, ini_file):
    # Beolvassuk a JSON fájlt
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Kiírjuk INI formátumban
    with open(ini_file, 'w', encoding='utf-8') as f:
        for key, value in data.items():
            # Ha a value üres string, akkor csak a kulcsot írjuk ki
            if value == "":
                f.write(f"{key}=\n")
            else:
                # Javítjuk a kódolást és a sortöréseket
                value = fix_encoding(value)
                value = fix_line_endings(value)
                
                # Ha több soros a szöveg, minden sort új sorba írunk
                if '\n' in value:
                    lines = value.split('\n')
                    f.write(f"{key}={lines[0]}\n")
                    for line in lines[1:]:
                        f.write(f"{line}\n")
                else:
                    f.write(f"{key}={value}\n")

if __name__ == "__main__":
    json_to_ini('tests/test_files/json/global_first100_test2.json', 
                'tests/test_files/ini/global_first100_hu_fromjson.ini')
