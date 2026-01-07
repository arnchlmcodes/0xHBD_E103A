"""
Quick test of the Document Q&A + LLM system
"""

from document_qa import DocumentQA
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize
print("Loading document...")
qa = DocumentQA(
    "ncert_maths_6-10/class6/json_output/fegp101.json",
    "ncert_maths_6-10/class6/fegp101.pdf"
)

# Test question
question = "What are triangular numbers? Give me examples."

print(f"\nQuestion: {question}")
print("\nRetrieving relevant content...")

# Get context
results = qa.ask(question, n_results=8)
context = qa.format_for_llm(results)

print(f"Found {len(results['all_results'])} relevant chunks")

# Show context
print("\n" + "=" * 70)
print("CONTEXT FOR LLM")
print("=" * 70)
print(context)

# Send to LLM
print("\n" + "=" * 70)
print("GENERATING ANSWER WITH LLM...")
print("=" * 70)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful mathematics tutor for Class 6 students."
        },
        {
            "role": "user",
            "content": f"""Use the following context to answer the question.

{context}

Provide a clear answer suitable for Class 6 students."""
        }
    ],
    temperature=0.3,
    max_tokens=512
)

answer = response.choices[0].message.content

print("\n" + "=" * 70)
print("FINAL ANSWER")
print("=" * 70)
print(answer)
print("=" * 70)

print("\n✅ Test complete!")
