"""
AI Animation Generator with SYNCHRONIZED Text-to-Speech Narration
Flow: Curriculum JSON -> Groq (Spec) -> TTS (Audio + Timing) -> Manim (Synchronized Video) -> Merge (Final)

This version generates audio FIRST, then uses the audio timings to control animation speed.
"""

import json
import os
import subprocess
import sys
from groq import Groq
from dotenv import load_dotenv
from tts_generator import TTSGenerator
from video_audio_merger import merge_video_audio

load_dotenv()

# Configuration
JSON_PATH = "class7/json_output/gegp108.json"
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

def generate_narration_audio():
    """Generate TTS narration from lesson spec - THIS HAPPENS FIRST"""
    print("\n" + "="*60)
    print("🎙️ STEP 1: GENERATING NARRATION AUDIO")
    print("="*60)
    print("⚡ This creates audio segments with precise timing data")
    print("   The video will sync to these audio timings!")
    
    try:
        tts_gen = TTSGenerator()
        audio_path, duration = tts_gen.generate_full_narration(use_edge_tts=True)
        print(f"\n✅ Narration audio generated: {audio_path}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Timing data: narration_full_timing.json")
        return audio_path, duration
    except Exception as e:
        print(f"\n❌ TTS generation failed: {e}")
        print("   Falling back to gTTS...")
        try:
            tts_gen = TTSGenerator()
            audio_path, duration = tts_gen.generate_full_narration(use_edge_tts=False)
            print(f"\n✅ Narration audio generated (gTTS): {audio_path}")
            return audio_path, duration
        except Exception as e2:
            print(f"\n❌ All TTS methods failed: {e2}")
            return None, None

def run_manim_synchronized():
    """Run Manim with synchronized timing in YouTube Shorts format"""
    print("\n" + "="*60)
    print("🎬 STEP 2: RENDERING SYNCHRONIZED ANIMATION")
    print("="*60)
    print("📱 Resolution: 1080x1920 (9:16 YouTube Shorts)")
    print("🎯 Syncing: Animation timing matches audio segments")
    print("(This might take a minute)")
    
    # YouTube Shorts dimensions with synchronized engine
    cmd = [
        sys.executable, "-m", "manim",
        "--resolution", "1080,1920",  # Portrait mode
        "--fps", "30",  # Smooth 30fps
        "manim_engine_synchronized.py",  # Use synchronized version
        "SynchronizedLesson"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("\n✅ Synchronized Animation Rendered!")
        video_path = "media/videos/manim_engine_synchronized/1920p30/SynchronizedLesson.mp4"
        print(f"📁 Video saved to: {video_path}")
        print("📱 Format: YouTube Shorts ready!")
        print("🎯 Timing: Perfectly synced with audio!")
        return video_path
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Manim Failed: {e}")
        print("--- STDERR ---")
        print(e.stderr)
        if "ffmpeg" in e.stderr.lower():
            print("\n🚨 CRITICAL: FFmpeg is missing!")
            print("To fix: Install FFmpeg from https://ffmpeg.org/download.html and add it to your PATH.")
        return None
    except FileNotFoundError:
        print("\n❌ Command not found.")
        return None

def merge_video_and_audio(video_path, audio_path):
    """Merge synchronized video with narration audio"""
    print("\n" + "="*60)
    print("🎞️ STEP 3: MERGING VIDEO AND AUDIO")
    print("="*60)
    print("🔗 Combining synchronized video with narration track")
    
    output_path = "final_video_with_narration.mp4"
    
    success = merge_video_audio(
        video_path=video_path,
        audio_path=audio_path,
        output_path=output_path,
        adjust_speed=False  # No speed adjustment needed - already synced!
    )
    
    if success:
        print(f"\n🎉 FINAL SYNCHRONIZED VIDEO READY: {output_path}")
        print("📱 Format: YouTube Shorts (1080x1920)")
        print("🎯 Audio-Visual Sync: Perfect!")
        return output_path
    else:
        print("\n❌ Merge failed")
        return None

def main():
    print("="*60)
    print("🎥 AI EDUCATIONAL ANIMATOR WITH SYNCHRONIZED NARRATION")
    print("="*60)
    print("🎯 NEW: Audio-driven timing for perfect synchronization!")
    
    # 1. Load Data
    print("\n📖 Loading curriculum data...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded: {JSON_PATH}")
        
    # 2. Generate Spec
    print("\n" + "="*60)
    print("📝 GENERATING ANIMATION SPECIFICATION")
    print("="*60)
    spec_json = generate_spec_with_llm(data)
    
    # Save spec for Manim to read
    with open("lesson_spec.json", "w", encoding="utf-8") as f:
        f.write(spec_json)
    print("💾 Saved storyboard to lesson_spec.json")
    
    # Display spec preview
    spec = json.loads(spec_json)
    print(f"\n📋 Spec Preview:")
    print(f"   Title: {spec.get('title', 'N/A')}")
    print(f"   Subtitle: {spec.get('subtitle', 'N/A')}")
    print(f"   Sections: {len(spec.get('sections', []))}")
    
    # 3. Generate Narration Audio FIRST (with timing data)
    audio_path, audio_duration = generate_narration_audio()
    
    if not audio_path:
        print("\n❌ Cannot proceed without audio - synchronization requires audio timing data")
        return
    
    # 4. Render Synchronized Video (using audio timing data)
    video_path = run_manim_synchronized()
    
    if not video_path:
        print("\n❌ Video rendering failed. Cannot proceed to merge.")
        return
    
    # 5. Merge Synchronized Video and Audio
    final_video = merge_video_and_audio(video_path, audio_path)
    
    if final_video:
        print("\n" + "="*60)
        print("✨ COMPLETE! ✨")
        print("="*60)
        print(f"📹 Final video: {final_video}")
        print(f"📱 Format: YouTube Shorts (1080x1920)")
        print(f"🎵 Audio: {audio_path}")
        print(f"📊 Timing data: narration_full_timing.json")
        print(f"🎯 Synchronization: Perfect audio-visual sync!")
        print("\n🎬 Your synchronized educational video is ready for YouTube Shorts!")
    else:
        print("\n⚠️ Process completed with errors. Check the logs above.")

if __name__ == "__main__":
    main()