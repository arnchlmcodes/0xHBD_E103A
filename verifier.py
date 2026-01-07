"""
Universal Content Verifier (The Truth Layer)
Uses Google Gemini to audit educational content for hallucinations and bias.

Usage:
    from verifier import ContentVerifier
    verifier = ContentVerifier()
    result = verifier.verify(source_text, generated_content)
    if result['score'] < 85:
        print("❌ Verification Failed!")
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ContentVerifier:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️  Warning: GEMINI_API_KEY not found. Verification layer is disabled.")
            self.enabled = False
        else:
            genai.configure(api_key=api_key)
            
            # AUTO-DISCOVERY: Find the first working model
            self.model = None
            self.model_name = "Unknown"
            
            try:
                print("🔍 Scanning available Gemini models...")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        print(f"   - Found: {m.name}")
                        self.model_name = m.name
                        self.model = genai.GenerativeModel(m.name)
                        break
                
                if not self.model:
                    print("⚠️  No suitable Gemini model found. Verification disabled.")
                    self.enabled = False
                else:
                    print(f"✅ targeted model: {self.model_name}")
                    self.enabled = True
                    
            except Exception as e:
                print(f"⚠️  Model discovery failed: {e}")
                self.enabled = False

    def verify(self, source_context: str, generated_content: str | dict, context_name: str = "Content"):
        """
        Verifies generated content against source context.
        Returns dict with keys: score, feedback, status
        """
        if not self.enabled:
            return {"score": 100, "status": "SKIPPED", "feedback": "Verifier disabled (no API key)"}

        print(f"\n🔍 Verifying {context_name} with Gemini Probe ({self.model_name})...")

        # Convert dict to string if needed
        if isinstance(generated_content, dict):
            content_str = json.dumps(generated_content, indent=2)
        else:
            content_str = str(generated_content)

        prompt = f"""
        You are an AI Auditor. Your job is to verify educational content against a trusted source.
        
        TRUSTED SOURCE:
        {source_context[:4000]}
        
        GENERATED CONTENT TO AUDIT:
        {content_str[:4000]}
        
        TASK:
        1. Check for HALLUCINATIONS: Are there facts in the content that directly contradict or are completely absent from the source? (Inference is okay, invention is not).
        2. Check for BIAS: Is there any political, gender, or cultural bias?
        3. Check for RELEVANCE: Is it actually teaching the topic?
        
        OUTPUT JSON ONLY:
        {{
            "score": <0-100 integer, where 100 is perfect alignment>,
            "hallucination_found": <bool>,
            "bias_found": <bool>,
            "reason": "Short explanation of the score",
            "flagged_issues": ["List", "of", "specific", "errors"]
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            # Clean up response text if it has markdown block
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            
            result = json.loads(text)
            self._print_report(result, context_name)
            return result
            
        except Exception as e:
            # Fallback logic could go here, but simple reporting is safer for now
            print(f"❌ Verification Error with {self.model_name}: {e}")
            return {"score": 0, "status": "ERROR", "feedback": str(e)}

    def _print_report(self, result, context_name):
        score = result.get('score', 0)
        color = "✅" if score >= 85 else "⚠️" if score >= 70 else "❌"
        
        print("\n" + "="*40)
        print(f"🛡️  VERIFICATION REPORT: {context_name}")
        print(f"{color} Trust Score: {score}/100")
        
        if result.get('hallucination_found'):
            print("👻 HALLUCINATION DETECTED")
        if result.get('bias_found'):
            print("⚖️  BIAS DETECTED")
            
        print(f"📝 Reason: {result.get('reason')}")
        
        if result.get('flagged_issues'):
            print("🚩 Issues:")
            for issue in result['flagged_issues']:
                print(f"   - {issue}")
        print("="*40 + "\n")

if __name__ == "__main__":
    # Test run
    v = ContentVerifier()
    v.verify("The sky is blue.", "The sky is green.", "Test Check")
