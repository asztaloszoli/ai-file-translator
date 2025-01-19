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
    # A \n karaktereket szóközre cseréljük
    text = text.replace('\\n', ' ')
    # Többszörös szóközöket egy szóközre cseréljük
    text = ' '.join(text.split())
    return text

def json_to_ini(json_file, ini_file):
    print(f"JSON fájl beolvasása: {json_file}")
    # Beolvassuk a JSON fájlt
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"JSON fájl sikeresen beolvasva, {len(data)} kulcs található benne")
    
    print(f"INI fájl létrehozása: {ini_file}")
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
                
                # Minden értéket egy sorba írunk
                f.write(f"{key}={value}\n")
    print(f"Az INI fájl sikeresen létrehozva: {ini_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Használat: python json_to_ini.py input.json output.ini")
        sys.exit(1)
    json_to_ini(sys.argv[1], sys.argv[2])
