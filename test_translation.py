from src.translation import batch_translate_texts

def test_translation():
    # Test text in French
    texts = ["Caméra d'Amarrage. (Basculer)"]
    
    # Translate to Hungarian
    translated = batch_translate_texts(texts, target_lang="Hungarian")
    
    print("\nTest Results:")
    print(f"Original: {texts[0]}")
    print(f"Translated: {translated[0]}")

if __name__ == "__main__":
    test_translation()
