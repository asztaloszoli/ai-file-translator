import os
import sys
import argparse
import logging
from datetime import datetime
from src.file_processors import process_file
from src.logging_config import setup_logging

def main():
    # Állítsuk be a konzol kódolását UTF-8-ra
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(
        description="Translate files using Anthropic's Claude AI model.",
        epilog="Example: python main.py --path /path/to/files --model claude-3-haiku-20240307 --default-lang en"
    )
    parser.add_argument("--path", default=os.getcwd(), help="Path to directory containing files to translate (default: current directory)")
    parser.add_argument("--model", default="claude-3-haiku-20240307", help="Anthropic model to use for translation (default: claude-3-haiku-20240307)")
    parser.add_argument("--default-lang", default="en", help="Default target language if not specified in filename (default: en)")
    args = parser.parse_args()

    print(f"Starting translation process for files in {args.path}")

    # Ellenőrizzük, hogy a megadott útvonal létezik-e
    if not os.path.exists(args.path):
        print(f"Error: Path does not exist: {args.path}")
        return

    # Ha a megadott útvonal egy fájl
    if os.path.isfile(args.path):
        print(f"\nProcessing single file: {args.path}")
        process_file(args.path, args.model, args.default_lang)
    else:
        # Ha a megadott útvonal egy könyvtár
        for root, _, files in os.walk(args.path):
            for filename in files:
                file_path = os.path.join(root, filename)
                print(f"\nProcessing file: {file_path}")
                process_file(file_path, args.model, args.default_lang)

    print("\nTranslation process completed")

if __name__ == "__main__":
    main()
