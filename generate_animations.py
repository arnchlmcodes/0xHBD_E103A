"""
AI Animation Generator
Flow: Curriculum JSON -> Groq (Spec) -> Manim (Video)

Usage:
    python generate_animations.py
"""

import json
import os
import subprocess
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configuration
JSON_PATH = "class7/json_output/gegp107.json"
TOPIC_INDEX = 0 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def generate_spec_with_llm(json_data):
    """Generate visual spec for Manim using Groq"""
    print("🤖 Designing animation storyboard...")
    
    topic = json_data[TOPIC_INDEX]
    topic_name = topic['topic_name']
    objectives = "\n".join([f"- {obj}" for obj in topic['learning_objectives']])
    content = "\n".join([b['text'] for b in topic['content_blocks']])[:2000]
    
    prompt = f"""
    Create a Manim animation specification for the topic: "{topic_name}".
    
    CONTEXT:
    {content}
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "title": "Short Title",
        "subtitle": "Short Subtitle",
        "sections": [
            {{
                "type": "definition",
                "term": "Key Term",
                "text": "Simple definition (max 10 words)"
            }},
            {{
                "type": "bullet_list",
                "heading": "Key Properties",
                "items": ["Point 1", "Point 2", "Point 3"]
            }},
            {{
                "type": "analogy",
                "concept": "Math Concept",
                "analogy": "Real world object"
            }},
            {{
                "type": "process",
                "steps": ["Step 1", "Step 2", "Step 3"]
            }},
            {{
                "type": "statement",
                "text": "Concluding thought"
            }}
        ]
    }}
    
    Make it visual, simple, and educational. Use 3-5 sections max.
    """
    
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a visual learning designer. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    return completion.choices[0].message.content

def run_manim():
    """Run Manim to render the video"""
    print("🎬 Rendering animation with Manim...")
    print("(This might take a minute)")
    
    # Use python -m manim to ensure we use the installed module
    import sys
    cmd = [sys.executable, "-m", "manim", "-ql", "manim_engine.py", "GeneratedLesson"]
    
    try:
        # Capture output to debug FFmpeg issues
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n✅ Animation Rendered Successfully!")
        print("📁 Look inside 'media/videos/manim_engine/480p15/GeneratedLesson.mp4'")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Manim Failed: {e}")
        print("--- STDERR ---")
        print(e.stderr)
        if "ffmpeg" in e.stderr.lower():
            print("\n🚨 CRITICAL: FFmpeg is missing!")
            print("To fix: Install FFmpeg from https://ffmpeg.org/download.html and add it to your PATH.")
    except FileNotFoundError:
        print("\n❌ Command not found.")

def main():
    print("="*60)
    print("🎥 AI EDUCATIONAL ANIMATOR")
    print("="*60)
    
    # 1. Load Data
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 2. Generate Spec
    spec_json = generate_spec_with_llm(data)
    
    # Save spec for Manim to read
    with open("lesson_spec.json", "w", encoding="utf-8") as f:
        f.write(spec_json)
    print("💾 Saved storyboard to lesson_spec.json")
    
    # 3. Render
    run_manim()

if __name__ == "__main__":
    main()
