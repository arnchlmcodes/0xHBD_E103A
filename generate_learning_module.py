"""
Modern Learning Module Generator
Generates a stunning, student-focused 8-page PDF learning module.

Structure:
1. Cover + Promise
2. Big Picture
3. Core Explanation
4. Analogy + Reality
5. Visual Thinking
6. Pause & Think
7. Practice
8. Summary

Usage:
    python generate_learning_module.py
"""

import json
import os
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Configuration
JSON_PATH = "class7/json_output/gegp105.json"
TOPIC_INDEX = 0  # Parallel and Intersecting Lines
PDFSHIFT_API_KEY = os.getenv("PDFSHIFT_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{topic_name}}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        body { 
            font-family: 'Outfit', sans-serif; 
            line-height: 1.6; 
            color: #2d3436; 
            margin: 0; 
            padding: 0; 
            background: #fdfdfd; 
        }
        
        .page { 
            width: 800px;
            height: 1100px; /* A4-ish ratio */
            margin: 0 auto; 
            padding: 60px; 
            box-sizing: border-box; 
            position: relative; 
            page-break-after: always;
            background: white;
            border-bottom: 1px solid #eee; /* For screen viewing */
        }
        
        /* Typography */
        h1 { font-weight: 800; font-size: 48px; line-height: 1.1; color: #2d3436; margin-bottom: 20px; }
        h2 { font-weight: 600; font-size: 32px; color: #0984e3; margin-top: 0; margin-bottom: 30px; }
        h3 { font-weight: 600; font-size: 24px; color: #2d3436; margin-top: 30px; margin-bottom: 15px; }
        p { font-size: 18px; color: #636e72; margin-bottom: 20px; }
        
        /* Components */
        .box { padding: 30px; border-radius: 12px; margin: 30px 0; }
        .box-blue { background: #e7f5ff; border-left: 6px solid #0984e3; }
        .box-purple { background: #f3f0ff; border-left: 6px solid #845ef7; }
        .box-yellow { background: #fff9db; border-left: 6px solid #fcc419; }
        
        .hook-text { font-size: 24px; font-weight: 300; color: #636e72; font-style: italic; }
        
        .list-clean { list-style: none; padding: 0; }
        .list-clean li { 
            font-size: 20px; 
            margin-bottom: 15px; 
            padding-left: 30px; 
            position: relative; 
        }
        .list-clean li:before { 
            content: "•"; 
            color: #0984e3; 
            font-size: 30px; 
            position: absolute; 
            left: 0; 
            top: -5px; 
        }
        
        .flow-step { 
            text-align: center; 
            font-size: 22px; 
            font-weight: 600; 
            padding: 15px; 
            border: 2px solid #dfe6e9; 
            border-radius: 8px; 
            margin: 10px 0; 
            background: white;
        }
        .flow-arrow { 
            text-align: center; 
            font-size: 24px; 
            color: #b2bec3; 
            margin: 5px 0; 
        }
        
        .question-card {
            background: #fff;
            border: 1px solid #dfe6e9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .footer {
            position: absolute;
            bottom: 40px;
            left: 60px;
            right: 60px;
            border-top: 1px solid #dfe6e9;
            padding-top: 20px;
            display: flex;
            justify-content: space-between;
            color: #b2bec3;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Cover Page Specifics */
        .cover-page { display: flex; flex-direction: column; justify-content: center; }
        .big-number { font-size: 120px; font-weight: 800; color: #f1f2f6; position: absolute; top: 20px; right: 20px; z-index: 0; }
        
    </style>
</head>
<body>

    <!-- PAGE 1: COVER + PROMISE -->
    <div class="page cover-page">
        <div class="big-number">01</div>
        <div style="z-index: 1;">
            <p style="text-transform: uppercase; letter-spacing: 2px; color: #0984e3; font-weight: 600;">Grade 7 Mathematics</p>
            <h1>{{topic_name}}</h1>
            <p class="hook-text">"{{hook}}"</p>
            
            <div class="box box-blue" style="margin-top: 60px;">
                <h3 style="margin-top: 0; color: #0984e3;">In this module, you will:</h3>
                <ul class="list-clean">
                    <li>Understand {{core_concept}}</li>
                    <li>See how it works in the real world</li>
                    <li>Master the basics in 10 minutes</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <span>Learning Module</span>
            <span>Page 1</span>
        </div>
    </div>

    <!-- PAGE 2: BIG PICTURE -->
    <div class="page">
        <div class="big-number">02</div>
        <h2>The Big Picture</h2>
        <p>Before we dive into details, let's understand what is really happening here.</p>
        
        <div style="margin-top: 40px;">
            <ul class="list-clean">
                {{big_picture_points}}
            </ul>
        </div>
        
        <div class="box box-yellow">
            <h3 style="margin-top: 0;">💡 Why this matters</h3>
            <p style="margin-bottom: 0;">{{why_it_matters}}</p>
        </div>

        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 2</span>
        </div>
    </div>

    <!-- PAGE 3: CORE EXPLANATION -->
    <div class="page">
        <div class="big-number">03</div>
        <h2>Core Concepts</h2>
        
        {{core_explanation}}
        
        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 3</span>
        </div>
    </div>

    <!-- PAGE 4: ANALOGY + REALITY -->
    <div class="page">
        <div class="big-number">04</div>
        <h2>Analogy & Reality</h2>
        
        <div class="box box-purple">
            <h3 style="margin-top: 0; color: #845ef7;">💭 Think of it like...</h3>
            <p style="margin-bottom: 0;">{{analogy}}</p>
        </div>
        
        <div class="box box-blue">
            <h3 style="margin-top: 0; color: #0984e3;">🔬 In Reality...</h3>
            <p style="margin-bottom: 0;">{{reality_check}}</p>
        </div>

        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 4</span>
        </div>
    </div>

    <!-- PAGE 5: VISUAL THINKING -->
    <div class="page">
        <div class="big-number">05</div>
        <h2>Visual Flow</h2>
        <p>Let's map this out simply.</p>
        
        <div style="margin: 60px 40px;">
            {{visual_flow}}
        </div>
        
        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 5</span>
        </div>
    </div>

    <!-- PAGE 6: PAUSE & THINK -->
    <div class="page">
        <div class="big-number">06</div>
        <h2>Pause & Think</h2>
        <p>Let's stop for a moment. Don't worry about getting the "right" answer yet.</p>
        
        <div class="box box-yellow" style="text-align: center; padding: 50px 30px;">
            <span style="font-size: 40px;">🧠</span>
            <h3 style="font-size: 28px; margin: 20px 0;">{{pause_question}}</h3>
            <p style="font-style: italic;">Take 30 seconds to think about this.</p>
        </div>

        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 6</span>
        </div>
    </div>

    <!-- PAGE 7: PRACTICE -->
    <div class="page">
        <div class="big-number">07</div>
        <h2>Quick Check</h2>
        <p>Let's see what you've got.</p>
        
        {{practice_questions}}
        
        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 7</span>
        </div>
    </div>

    <!-- PAGE 8: SUMMARY -->
    <div class="page">
        <div class="big-number">08</div>
        <h2>Key Takeaways</h2>
        
        <div class="box box-blue">
            <ul class="list-clean">
                {{summary_points}}
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 60px;">
            <h3 style="font-size: 32px; color: #27ae60;">✅ Confidence Boost</h3>
            <p>{{confidence_boost}}</p>
        </div>

        <div class="footer">
            <span>{{topic_name}}</span>
            <span>Page 8</span>
        </div>
    </div>

</body>
</html>
"""

def generate_module_content(json_data):
    """Generate modern learning content using LLM"""
    print("🤖 Generating modern learning content...")
    
    topic = json_data[TOPIC_INDEX]
    topic_name = topic['topic_name']
    objectives = "\n".join([f"- {obj}" for obj in topic['learning_objectives']])
    content_text = "\n".join([b['text'] for b in topic['content_blocks']])
    
    prompt = f"""
    You are creating a MODERN LEARNING PDF for Grade 7 students.
    Topic: "{topic_name}"
    
    SOURCE MATERIAL:
    {content_text[:2500]}
    
    RULES:
    1. Tone: Friendly, direct, active voice ("You"). No "Thus" or "Therefore".
    2. Structure: Short sentences. One idea per line.
    3. Analogy: Must be relatable to a 12-year-old.
    
    Return JSON with these exact keys:
    {{
        "hook": "A 1-sentence curiosity hook (e.g. 'Ever wondered...')",
        "core_concept": "The main thing they will learn (3-4 words)",
        "big_picture_points": ["Simple point 1", "Simple point 2", "Simple point 3"],
        "why_it_matters": "One sentence on why this is useful in real life",
        "core_explanation": [
            {{"title": "Subheading 1", "text": "Short explanation (max 2 sentences)"}},
            {{"title": "Subheading 2", "text": "Short explanation (max 2 sentences)"}},
            {{"title": "Subheading 3", "text": "Short explanation (max 2 sentences)"}}
        ],
        "analogy": "A relatable analogy (e.g. 'Examples of parallel lines like railway tracks')",
        "reality_check": "The scientific/math concept explained simply",
        "visual_flow": ["Step 1", "Step 2", "Step 3", "Step 4"],
        "pause_question": "A deep thinking question (no easy answer)",
        "practice_questions": [
            {{"q": "Simple recall question?", "a": "Answer"}},
            {{"q": "Thinking question?", "a": "Answer"}}
        ],
        "summary_points": ["Key takeaway 1", "Key takeaway 2", "Key takeaway 3"],
        "confidence_boost": "A closing sentence telling them they did great."
    }}
    """
    
    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a world-class educational content creator. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    return json.loads(completion.choices[0].message.content)

def create_html(json_data, content):
    """Fill the modern HTML template"""
    print("📝 Assembling PDF layout...")
    
    topic = json_data[TOPIC_INDEX]
    html = HTML_TEMPLATE.replace("{{topic_name}}", topic['topic_name'])
    
    # Page 1
    html = html.replace("{{hook}}", content['hook'])
    html = html.replace("{{core_concept}}", content['core_concept'])
    
    # Page 2
    bp_html = "\n".join([f"<li>{pt}</li>" for pt in content['big_picture_points']])
    html = html.replace("{{big_picture_points}}", bp_html)
    html = html.replace("{{why_it_matters}}", content['why_it_matters'])
    
    # Page 3
    exp_html = ""
    for section in content['core_explanation']:
        exp_html += f"<h3>{section['title']}</h3><p>{section['text']}</p>"
    html = html.replace("{{core_explanation}}", exp_html)
    
    # Page 4
    html = html.replace("{{analogy}}", content['analogy'])
    html = html.replace("{{reality_check}}", content['reality_check'])
    
    # Page 5
    flow_html = ""
    for i, step in enumerate(content['visual_flow']):
        flow_html += f'<div class="flow-step">{step}</div>'
        if i < len(content['visual_flow']) - 1:
            flow_html += '<div class="flow-arrow">↓</div>'
    html = html.replace("{{visual_flow}}", flow_html)
    
    # Page 6
    html = html.replace("{{pause_question}}", content['pause_question'])
    
    # Page 7
    q_html = ""
    for q in content['practice_questions']:
        q_html += f"""
        <div class="question-card">
            <h3 style="margin-top:0;">❓ {q['q']}</h3>
            <p style="margin-bottom:0; color: #b2bec3; font-size: 14px;">Answer: {q['a']}</p>
        </div>
        """
    html = html.replace("{{practice_questions}}", q_html)
    
    # Page 8
    sum_html = "\n".join([f"<li>{pt}</li>" for pt in content['summary_points']])
    html = html.replace("{{summary_points}}", sum_html)
    html = html.replace("{{confidence_boost}}", content['confidence_boost'])
    
    return html

def convert_to_pdf(html_content):
    """Convert to PDF"""
    print("🚀 Generating Modern PDF...")
    
    if not PDFSHIFT_API_KEY:
        print("⚠️  No API Key. Saving as HTML.")
        with open("learning_module.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ Saved to learning_module.html")
        return

    response = requests.post(
        "https://api.pdfshift.io/v3/convert/pdf",
        auth=("api", PDFSHIFT_API_KEY),
        json={
            "source": html_content,
            "landscape": False, 
            "margin": "0px", # Full bleed for modern look
            "format": "A4"
        }
    )

    if response.status_code == 200:
        with open("learning_module.pdf", "wb") as f:
            f.write(response.content)
        print("✅ Success! Saved to learning_module.pdf")
    else:
        print(f"❌ Error: {response.text}")
        with open("learning_module.html", "w", encoding="utf-8") as f:
            f.write(html_content)

def main():
    print("="*60)
    print("📑 MODERN LEARNING MODULE GENERATOR")
    print("="*60)
    
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    content = generate_module_content(data)
    html = create_html(data, content)
    convert_to_pdf(html)

if __name__ == "__main__":
    main()
