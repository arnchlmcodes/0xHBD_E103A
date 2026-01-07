import json
from jsonschema import validate

def validate_json(json_file, schema_file):
    with open(json_file) as f:
        data = json.load(f)
    with open(schema_file) as f:
        schema = json.load(f)

    validate(instance=data, schema=schema)
    print("JSON is valid.")

if __name__ == "__main__":
    validate_json("ert_curriculum.json", "curriculum_schema.json")
