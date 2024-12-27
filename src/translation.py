import anthropic
import re
import os
import tiktoken
from typing import List, Tuple

def print_safe(text: str):
    """Biztonságos kiírás, ami kezeli a kódolási hibákat"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode())

def count_tokens(text: str) -> int:
    """Megszámolja a tokenek számát egy szövegben"""
    try:
        enc = tiktoken.encoding_for_model("claude-2")
        return len(enc.encode(text))
    except:
        # Ha nem sikerül pontosan számolni, becsüljük a szavak száma alapján
        return len(text.split()) * 2

def estimate_cost(texts: List[str]) -> Tuple[float, float]:
    """Költségbecslés a szövegek alapján"""
    total_input_tokens = sum(count_tokens(text) for text in texts)
    # Becsült output tokenek (általában 1.2x hosszabb a fordítás)
    total_output_tokens = int(total_input_tokens * 1.2)
    
    # Haiku model árak
    input_cost = (total_input_tokens / 1_000_000) * 0.25  # $0.25/1M token
    output_cost = (total_output_tokens / 1_000_000) * 1.25  # $1.25/1M token
    
    return input_cost, output_cost

def batch_translate_texts(texts: List[str], target_lang: str, model: str = 'claude-2', batch_size: int = 10) -> List[str]:
    """
    Szövegek fordítása batch-ekben
    :param texts: Fordítandó szövegek listája
    :param target_lang: Célnyelv
    :param model: AI modell neve
    :param batch_size: Egy batch-ben hány szöveget fordítsunk
    :return: Lefordított szövegek listája
    """
    print_safe("\nInitializing translation...")
    
    # Az Anthropic API kulcsot itt kell beírni. Az API kulcs az Anthropic fiókodhoz tartozik, és a fordítási kérelmek hitelesítésére szolgál.
    api_key = ""
    print_safe("API key loaded successfully")
    
    try:
        client = anthropic.Client(api_key=api_key)
    except Exception as e:
        print_safe(f"Error initializing Anthropic client: {str(e)}")
        return texts
    
    # Költségbecslés
    total_texts = len(texts)
    total_batches = (total_texts + batch_size - 1) // batch_size
    print_safe(f"\nTotal texts to translate: {total_texts}")
    print_safe(f"Will process in {total_batches} batches of {batch_size} texts each")
    
    input_cost, output_cost = estimate_cost(texts)
    total_cost = input_cost + output_cost
    print_safe(f"\nEstimated costs:")
    print_safe(f"Input cost: ${input_cost:.3f}")
    print_safe(f"Output cost: ${output_cost:.3f}")
    print_safe(f"Total estimated cost: ${total_cost:.3f}")
    
    # Ha a költség $1 alatt van, automatikusan elfogadjuk
    if total_cost < 1.0:
        print_safe("\nCost is under $1, automatically proceeding with translation...")
        response = 'y'
    else:
        response = 'y'  # Automatikusan elfogadjuk a fordítást
        print_safe("\nAutomatically proceeding with translation...")
    
    if response.lower() != 'y':
        print_safe("Translation cancelled by user")
        return texts
    
    # Összeállítjuk a prompt-ot
    system_prompt = """You are a professional translator. Follow these rules when translating from French to Hungarian:
1. Keep technical terms and proper nouns (like HDPC, Hangar, Cargo) unchanged
2. Use appropriate gaming terminology
3. Keep the translation natural but maintain the sci-fi atmosphere
4. ONLY return the translation, no explanations
5. Keep the same formatting (capitalization, punctuation)"""
    
    translated_texts = []
    current_cost = 0.0
    
    # Batch-ekben fordítjuk a szövegeket
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print_safe(f"\nProcessing batch {i//batch_size + 1}/{total_batches}")
        
        batch_translations = []
        for text in batch:
            if not text.strip():
                batch_translations.append(text)
                continue
            
            # Ha a szöveg egy TextBlock objektum stringje, vegyük ki belőle a szöveget
            if isinstance(text, str) and "[TextBlock" in text:
                try:
                    text_start = text.find('text=') + 6
                    text_end = text.find("', type=") if "', type=" in text else text.find('", type=')
                    if text_start > 5 and text_end > text_start:
                        text = text[text_start:text_end].strip('"\'')
                except:
                    pass
            
            try:
                print_safe(f"\nTranslating text: {text}")
                
                message = client.messages.create(
                    model=model,
                    max_tokens=1000,
                    temperature=0,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": f"Translate this French text to Hungarian:\n\n{text}"
                    }]
                )
                
                translated_text = message.content[0].text.strip()
                print_safe(f"Original: {text}")
                print_safe(f"Translated: {translated_text}")
                batch_translations.append(translated_text)
                
                # Költség számítás
                input_tokens = count_tokens(text)
                output_tokens = count_tokens(translated_text)
                batch_cost = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)
                current_cost += batch_cost
                
            except Exception as e:
                print_safe(f"Error translating text: {str(e)}")
                print_safe("Using original text instead")
                batch_translations.append(text)
        
        translated_texts.extend(batch_translations)
        
        # Minden 10. batch után költségjelentés
        if (i//batch_size + 1) % 10 == 0:
            print_safe(f"\nProgress: {len(translated_texts)}/{total_texts} texts translated")
            print_safe(f"Current cost: ${current_cost:.3f}")
            print_safe(f"Estimated remaining cost: ${(total_cost - current_cost):.3f}")
    
    print_safe(f"\nTranslation completed!")
    print_safe(f"Final cost: ${current_cost:.3f}")
    
    return translated_texts
