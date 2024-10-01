import unittest
import os
import json
import xml.etree.ElementTree as ET
from src.language_utils import get_target_language
from src.translation import batch_translate_texts
from src.file_processors import (
    process_json,
    process_xml,
    process_xliff,
    process_text,
    process_markdown
)

class TestTranslation(unittest.TestCase):

    def setUp(self):
        self.test_files_dir = os.path.join(os.path.dirname(__file__), 'test_files')
        self.model = "claude-3-haiku-20240307"
        
        # Reset test files to English
        self.reset_test_files()

    def reset_test_files(self):
        # Reset markdown file
        md_content = """# Welcome to Our Documentation

## Introduction

This is a sample Markdown file for testing translation capabilities. Markdown is widely used for documentation and readme files.

## Features

- **Easy to read**: Markdown files are easy to read in their raw format.
- **Versatile**: Can be converted to many other formats like HTML.
- **Lightweight**: Markdown files are small in size.

## Code Example

Here's a simple Python function:

```python
def greet(name):
    return f"Hello, {name}!"
```

## Conclusion

Markdown is an excellent choice for creating documentation. It's simple, yet powerful.

For more information, visit [our website](https://www.example.com).
"""
        with open(os.path.join(self.test_files_dir, 'markdown', 'test_file.md'), 'w', encoding='utf-8') as f:
            f.write(md_content)

        # Reset text file
        txt_content = """Welcome to Our Product

Our product is designed to make your life easier. Here are some key features:

1. Simple and intuitive interface
2. Powerful data analysis tools
3. Seamless integration with other platforms

If you have any questions, please don't hesitate to contact our support team at support@example.com.

Thank you for choosing our product!
"""
        with open(os.path.join(self.test_files_dir, 'txt', 'test_file.txt'), 'w', encoding='utf-8') as f:
            f.write(txt_content)

        # Reset XLIFF file
        xliff_content = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file source-language="en" target-language="es" datatype="plaintext" original="test_file">
    <header>
      <tool tool-id="ai-translator" tool-name="AI Translator"/>
    </header>
    <body>
      <trans-unit id="1">
        <source>Welcome to our application</source>
        <target></target>
      </trans-unit>
      <trans-unit id="2">
        <source>Please enter your username and password to log in.</source>
        <target></target>
      </trans-unit>
      <trans-unit id="3">
        <source>Forgot your password?</source>
        <target></target>
      </trans-unit>
    </body>
  </file>
</xliff>
"""
        with open(os.path.join(self.test_files_dir, 'xliff', 'test_file.xlf'), 'w', encoding='utf-8') as f:
            f.write(xliff_content)

        # Reset JSON file
        json_content = {
            "content": {
                "title": "Welcome to Our Website",
                "description": "This is a sample description for testing purposes.",
                "features": [
                    "Easy to use interface",
                    "Powerful search functionality",
                    "Responsive design"
                ]
            }
        }
        with open(os.path.join(self.test_files_dir, 'json', 'test_file.json'), 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False, indent=2)

        # Reset XML file
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<website>
  <header>
    <title>Welcome to Our Website</title>
    <subtitle>Discover Amazing Features</subtitle>
  </header>
  <content>
    <paragraph>This is a sample paragraph for testing XML translation.</paragraph>
    <features>
      <item>User-friendly interface</item>
      <item>Advanced search capabilities</item>
      <item>Mobile-responsive design</item>
    </features>
  </content>
  <footer>
    <copyright>© 2024 Example Company. All rights reserved.</copyright>
  </footer>
</website>
"""
        with open(os.path.join(self.test_files_dir, 'xml', 'test_file.xml'), 'w', encoding='utf-8') as f:
            f.write(xml_content)

    def test_get_target_language(self):
        self.assertEqual(get_target_language('file_es.json', 'en'), 'es')
        self.assertEqual(get_target_language('file.json', 'en'), 'en')
        self.assertEqual(get_target_language('file_fra.txt', 'en'), 'fr')
        self.assertEqual(get_target_language('file_invalid.txt', 'en'), 'en')

    def test_batch_translate_texts(self):
        texts = ["Hello, world!", "How are you?"]
        translated = batch_translate_texts(texts, 'es', self.model)
        self.assertEqual(len(translated), len(texts))
        self.assertNotEqual(translated[0], texts[0])
        self.assertNotEqual(translated[1], texts[1])

    def test_process_json(self):
        json_file = os.path.join(self.test_files_dir, 'json', 'test_file.json')
        process_json(json_file, 'content', self.model, 'es')
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertIn('content', data)
        self.assertNotEqual(data['content']['title'], "Welcome to Our Website")
        self.assertNotEqual(data['content']['description'], "This is a sample description for testing purposes.")
        self.assertNotEqual(data['content']['features'][0], "Easy to use interface")

    def test_process_xml(self):
        xml_file = os.path.join(self.test_files_dir, 'xml', 'test_file.xml')
        process_xml(xml_file, self.model, 'es')
        tree = ET.parse(xml_file)
        root = tree.getroot()
        title = root.find('.//title').text
        self.assertNotEqual(title, "Welcome to Our Website")
        paragraph = root.find('.//paragraph').text
        self.assertNotEqual(paragraph, "This is a sample paragraph for testing XML translation.")
        features = root.findall('.//item')
        self.assertEqual(len(features), 3)
        for item in features:
            self.assertNotIn("Text", item.text)

    def test_process_xliff(self):
        xliff_file = os.path.join(self.test_files_dir, 'xliff', 'test_file.xlf')
        process_xliff(xliff_file, self.model, 'es')
        tree = ET.parse(xliff_file)
        root = tree.getroot()
        targets = root.findall('.//{urn:oasis:names:tc:xliff:document:1.2}target')
        self.assertTrue(len(targets) > 0, "No target elements found")
        for target in targets:
            self.assertIsNotNone(target.text, "Target element has no text")
            self.assertNotEqual(target.text.strip(), "", "Target element text is empty")
        # Check if the first target is translated
        first_target = targets[0].text
        self.assertNotEqual(first_target, "Welcome to our application")

    def test_process_text(self):
        txt_file = os.path.join(self.test_files_dir, 'txt', 'test_file.txt')
        with open(txt_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        translated_content = process_text(txt_file, self.model, 'es')
        self.assertNotEqual(original_content, translated_content, "Content was not translated")
        with open(txt_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        self.assertEqual(translated_content, file_content, "Translated content was not written to file")
        self.assertNotIn("Welcome to Our Product", translated_content)

    def test_process_markdown(self):
        md_file = os.path.join(self.test_files_dir, 'markdown', 'test_file.md')
        with open(md_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        process_markdown(md_file, self.model, 'es')
        with open(md_file, 'r', encoding='utf-8') as f:
            translated_content = f.read()
        self.assertNotEqual(original_content, translated_content, "Content was not translated")
        self.assertNotIn("Welcome to Our Documentation", translated_content)
        self.assertIn("```python", translated_content)  # Check if code block is preserved
        self.assertIn("def greet(name):", translated_content)  # Check if code content is not translated

if __name__ == '__main__':
    unittest.main()
