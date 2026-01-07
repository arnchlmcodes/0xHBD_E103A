import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.1-8b-instant"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PDF_FILE = r"ncert_maths_6-10\class6\fegp101.pdf"
TEXT_FILE = r"ncert_maths_6-10\class6\fegp101.txt"
OUTPUT_FILE = "hacktide.json"

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an information extraction system. "
                    "Return VALID JSON ONLY with a single top-level key called 'chunks'."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content


def build_final_json(raw_json):
    extracted = json.loads(raw_json)

    document_id = os.path.splitext(os.path.basename(PDF_FILE))[0]

    return {
        "document_id": document_id,
        "source": PDF_FILE,
        "unit": document_id,
        "chunks": extracted.get("chunks", [])
    }


if __name__ == "__main__":
    text = load_file(TEXT_FILE)

    prompt = f"""
Rules:
- DO NOT add new information
- DO NOT paraphrase
- ONLY extract curriculum content
- Output JSON with exactly ONE key: "chunks"

Each chunk MUST contain:
- chunk_id
- topic
- learning_objective
- text

Text:
{text}
"""

    raw_output = call_llm(prompt)
    final_json = build_final_json(raw_output)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2)

    print("✅ Free API JSON saved (Groq)")
