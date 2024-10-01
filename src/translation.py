import anthropic
import logging
import re
from typing import List

def batch_translate_texts(texts: List[str], target_lang: str, model: str) -> List[str]:
    client = anthropic.Anthropic()
    translated_texts = []
    
    for text in texts:
        if not text.strip():  # Skip empty or whitespace-only strings
            translated_texts.append(text)
            continue
        
        try:
            system_prompt = f"""You are a translator. Translate the following text to {target_lang}. 
            Maintain the original structure, formatting, and any markup or special syntax.
            Do not add any additional text or explanations."""

            message = client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": text}
                ]
            )

            response_content = message.content
            if isinstance(response_content, list) and len(response_content) > 0:
                text_block = response_content[0]
                if hasattr(text_block, 'text'):
                    translated_text = text_block.text
                else:
                    translated_text = str(text_block)
            else:
                translated_text = str(response_content)

            translated_texts.append(translated_text)
            logging.debug(f"Translated text (first 100 chars): {translated_text[:100]}...")

        except Exception as e:
            logging.error(f"Translation error: {e}")
            logging.exception("Exception details:")
            translated_texts.append(text)  # Use original text if translation fails

    return translated_texts
