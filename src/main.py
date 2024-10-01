import os
import argparse
import logging
from datetime import datetime
from src.logging_config import setup_logging
from src.file_processors import process_file

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
