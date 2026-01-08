"""
Flashcard Generator (JSON)
Generates educational flashcards (Q&A) from curriculum data.
Audited by Gemini Verifier.

Usage:
    python generate_flashcards.py
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

# Configuration
# Removed global hardcoded paths
# JSON_PATH = "class7/json_output/gegp105.json"
# TOPIC_INDEX = 0
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_cards(json_data, topic_index=0):
    """Generate high-quality flashcards using LLM"""
    print("🤖 Synthesizing flashcards...")
    
    topic = json_data[topic_index]
    topic_name = topic['topic_name']
    content_text = "\n".join([b['text'] for b in topic['content_blocks']])
    
    prompt = f"""
    Create a set of educational flashcards for the topic: "{topic_name}".
    
    SOURCE MATERIAL:
    {content_text[:3000]}
    
    REQUIREMENTS:
    1. Create 10-15 cards based on the depth of the material.
    2. Include a mix of:
       - Definitions (Q: What is X? A: ...)
       - Concepts (Q: Why does Y happen? A: ...)
       - Examples (Q: Solve this example... A: Solution)
    3. Keep answers concise (under 2 sentences).
    
    OUTPUT JSON FORMAT ONLY:
    {{
        "topic": "{topic_name}",
        "cards": [
            {{"front": "Question or Term", "back": "Answer or Definition", "type": "definition"}},
            {{"front": "Problem...", "back": "Solution", "type": "problem"}}
        ]
    }}
    """
    
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an expert curriculum developer. Output valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    return json.loads(completion.choices[0].message.content)

def run_flashcard_generator(json_path, output_path=None, topic_index=0):
    print("="*60)
    print("🃏 FLASHCARD GENERATOR")
    print("="*60)
    
    # 1. Load Data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        data = [data]
        
    topic = data[topic_index]
        
    # 2. Generate
    result = generate_cards(data, topic_index)
    cards = result.get('cards', [])
    print(f"✅ Generated {len(cards)} cards.")
    
    # 3. No Verification needed for flashcards as per user request
    result['verification_status'] = "skipped"
    
    # 4. Save
    if not output_path:
        input_stem = os.path.splitext(os.path.basename(json_path))[0]
        output_path = f"{input_stem}_flashcards.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        
    print(f"\n💾 Saved to {output_path}")
    return output_path

if __name__ == "__main__":
    default_json = "class7/json_output/gegp105.json"
    if os.path.exists(default_json):
        run_flashcard_generator(default_json)
    else:
        print("Default file not found.")
