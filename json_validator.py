import json
import sys

def validate_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            try:
                json.loads(content)
                print("JSON is valid!")
            except json.JSONDecodeError as e:
                print(f"\nJSON Error at line {e.lineno}, column {e.colno}:")
                lines = content.split('\n')
                # Show 3 lines before and after the error
                start = max(0, e.lineno - 4)
                end = min(len(lines), e.lineno + 3)
                for i in range(start, end):
                    prefix = "-> " if i == e.lineno - 1 else "   "
                    print(f"{prefix}{i+1}: {lines[i]}")
                print(f"\nError message: {str(e)}")
    except Exception as e:
        print(f"Error reading file: {str(e)}")

if __name__ == "__main__":
    validate_json("tests/test_files/json/test1_hu.json")
