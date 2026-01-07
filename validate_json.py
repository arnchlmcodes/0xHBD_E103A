import json
import os
from jsonschema import validate, ValidationError

def validate_json(json_file, schema_file):
    if not os.path.exists(json_file):
        raise FileNotFoundError(
            f"JSON file not found: {json_file}\n"
            f"Please run 'ai_text_to_json.py' first to create the JSON file with chunks."
        )
    
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=data, schema=schema)
        print("✅ JSON is valid.")
        print(f"   Document ID: {data.get('document_id', 'N/A')}")
        print(f"   Number of chunks: {len(data.get('chunks', []))}")
    except ValidationError as e:
        print(f"❌ JSON validation failed:")
        print(f"   {e.message}")
        if e.path:
            print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        raise

if __name__ == "__main__":
    validate_json("ert_curriculum.json", "curriculum_schema.json")
