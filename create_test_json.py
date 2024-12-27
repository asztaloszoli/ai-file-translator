import json

# Beolvassuk az eredeti JSON fájlt
with open('tests/test_files/json/global.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Kiválasztjuk az első 100 kulcs-érték párt
first_100 = dict(list(data.items())[:100])

# Elmentjük az új JSON fájlba
with open('tests/test_files/json/global_first100_test.json', 'w', encoding='utf-8') as f:
    json.dump(first_100, f, ensure_ascii=False, indent=2)
