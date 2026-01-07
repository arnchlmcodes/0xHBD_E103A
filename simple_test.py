"""
SIMPLE TEST - Just run this to see if everything works!
"""

print("=" * 70)
print("🧪 SIMPLE TEST - Document Q&A System")
print("=" * 70)

print("\n[1/4] Importing modules...")
try:
    from document_qa import DocumentQA
    from groq import Groq
    import os
    from dotenv import load_dotenv
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Missing module: {e}")
    print("\nPlease install: pip install sentence-transformers chromadb groq python-dotenv")
    exit(1)

print("\n[2/4] Loading environment...")
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    print("❌ GROQ_API_KEY not found in .env file")
    print("   Please add it to your .env file")
    exit(1)
print("✅ API key loaded")

print("\n[3/4] Loading document...")
try:
    qa = DocumentQA(
        "ncert_maths_6-10/class6/json_output/fegp101.json",
        "ncert_maths_6-10/class6/fegp101.pdf"
    )
    print("✅ Document loaded successfully")
except Exception as e:
    print(f"❌ Error loading document: {e}")
    exit(1)

print("\n[4/4] Testing Q&A...")
question = "What are triangular numbers?"
print(f"   Question: {question}")

try:
    # Get context
    results = qa.ask(question, n_results=5)
    print(f"   ✅ Found {len(results['all_results'])} relevant chunks")
    
    # Show a sample result
    if results["content_blocks"]:
        sample = results["content_blocks"][0]
        print(f"\n   Sample result:")
        print(f"   Type: {sample['metadata']['doc_type']}")
        print(f"   Relevance: {sample['relevance_score']:.1%}")
        print(f"   Text: {sample['text'][:100]}...")
    
    # Test LLM integration
    print("\n[5/5] Testing LLM integration...")
    context = qa.format_for_llm(results)
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful math tutor."
            },
            {
                "role": "user",
                "content": f"{context}\n\nProvide a brief answer (2-3 sentences)."
            }
        ],
        temperature=0.3,
        max_tokens=200
    )
    
    answer = response.choices[0].message.content
    print("   ✅ LLM response received")
    
    print("\n" + "=" * 70)
    print("📖 QUESTION")
    print("=" * 70)
    print(question)
    
    print("\n" + "=" * 70)
    print("💡 ANSWER FROM LLM")
    print("=" * 70)
    print(answer)
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nYour system is working correctly! 🎉")
    print("\nNext steps:")
    print("  1. Try interactive mode: python document_qa.py")
    print("  2. See more examples: python demo_document_qa.py")
    print("  3. Read the guide: HOW_TO_USE.md")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
