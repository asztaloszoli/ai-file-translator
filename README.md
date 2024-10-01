# AI File Translator

This script uses Anthropic's Claude AI model to translate files in various formats (JSON, XML, XLIFF, TXT, and Markdown) to a specified target language.

## Features

Supports multiple file formats:
- JSON
- XML
- XLIFF
- TXT
- Markdown

## Requirements

- Python 3.6+
- Anthropic API key

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/sidedwards/ai-file-translator.git
   cd ai-file-translator
   ```

2. Run the setup script:
   ```
   ./setup.sh
   ```

3. Edit the `.env` file and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```

5. Run the script:
   ```
   python run.py --path /path/to/files --model claude-3-haiku-20240307 --default-lang en
   ```

## Usage

```
python run.py [--path PATH] [--model MODEL] [--default-lang LANG]
```

### Arguments

- `--path`: Path to the directory containing files to translate (default: current directory)
- `--model`: Anthropic model to use for translation (default: claude-3-haiku-20240307)
- `--default-lang`: Default target language if not specified in filename (default: en)

For more information, run:

```
python run.py --help
```

## Project Structure

```
ai-file-translator/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── file_processors.py
│   ├── translation.py
│   └── language_utils.py
├── logs/
├── tests/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── setup.sh
```

## Supported File Formats

- JSON: Translates specified nodes within the JSON structure
- XML: Translates all text content within XML tags
- XLIFF: Translates source texts in XLIFF files
- TXT: Translates the entire content of text files
- Markdown: Translates Markdown content while preserving code blocks and links

## Logs

Detailed logs are stored in the `logs` directory, with each run creating a new timestamped log file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
