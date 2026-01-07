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
from verifier import ContentVerifier

load_dotenv()

# Configuration
JSON_PATH = "class7/json_output/gegp105.json"
TOPIC_INDEX = 0
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_cards(json_data):
    """Generate high-quality flashcards using LLM"""
    print("🤖 Synthesizing flashcards...")
    
    topic = json_data[TOPIC_INDEX]
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
    
    client = Groq(api_key=GROQ_API_KEY)
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

def main():
    print("="*60)
    print("🃏 FLASHCARD GENERATOR")
    print("="*60)
    
    # 1. Load Data
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        topic = data[TOPIC_INDEX]
        
    # 2. Generate
    result = generate_cards(data)
    cards = result.get('cards', [])
    print(f"✅ Generated {len(cards)} cards.")
    
    # 3. Verify
    print("\n🛡️  Auditing cards with Gemini Verifier...")
    verifier = ContentVerifier()
    source_text = "\n".join([b['text'] for b in topic['content_blocks']])
    
    # Verify the entire set as a text block
    cards_text = json.dumps(cards, indent=2)
    report = verifier.verify(source_text, cards_text, context_name="Flashcards")
    
    if report.get('score', 0) < 70:
        print("❌ CARDS REJECTED: Score too low.")
        # We save them anyway marked as 'rejected' for debug
        result['verification_status'] = "rejected"
    else:
        result['verification_status'] = "verified"
        
    result['verification_report'] = report
    
    # 4. Save
    # Derive filename from input JSON (e.g. gegp105.json -> gegp105_flashcards.json)
    input_stem = os.path.splitext(os.path.basename(JSON_PATH))[0]
    output_filename = f"{input_stem}_flashcards.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        
    print(f"\n💾 Saved to {output_filename}")

if __name__ == "__main__":
    main()
