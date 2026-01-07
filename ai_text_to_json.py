import json
import os
from groq import Groq
from dotenv import load_dotenv
import pdfplumber
import re

load_dotenv()

MODEL = "llama-3.1-8b-instant"
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Token limits - leaving buffer for prompt overhead
# API limit is 6000 tokens, but we need to account for:
# - System prompt (~50 tokens)
# - User prompt template (~150 tokens)
# - Response tokens (~500 tokens estimated)
# So we reserve ~4000 tokens for the actual text content
MAX_TOKENS_FOR_TEXT = 4000  # Very conservative limit
CHARS_PER_TOKEN = 3.5  # More conservative estimate (some text has more tokens per char)
MAX_CHARS_PER_CHUNK = int(MAX_TOKENS_FOR_TEXT * CHARS_PER_TOKEN)  # ~14000 chars

PDF_FILE = os.path.join("ncert_maths_6-10", "class6", "fegp101.pdf")
TEXT_FILE = os.path.join("ncert_maths_6-10", "class6", "fegp101.txt")
OUTPUT_FILE = "ert_curriculum.json"

def convert_pdf_to_text(pdf_path, txt_path):
    """Convert PDF to text file if it doesn't exist."""
    print(f"Converting PDF to text: {pdf_path}")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"✅ PDF text extracted successfully: {txt_path}")

def load_file(path, pdf_path=None):
    """Load text file, converting from PDF if necessary."""
    if not os.path.exists(path):
        if pdf_path and os.path.exists(pdf_path):
            convert_pdf_to_text(pdf_path, path)
        else:
            raise FileNotFoundError(f"File not found: {path}\nPDF file also not found: {pdf_path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text, max_chars=MAX_CHARS_PER_CHUNK):
    """Split text into chunks, trying to break at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs (double newlines)
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        # If adding this paragraph would exceed limit, save current chunk and start new one
        if current_chunk and len(current_chunk) + len(para) + 2 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
        
        # If a single paragraph is too large, split it by sentences
        if len(current_chunk) > max_chars:
            sentences = re.split(r'(?<=[.!?])\s+', current_chunk)
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) + 1 > max_chars:
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
                    temp_chunk = sentence
                else:
                    temp_chunk += " " + sentence if temp_chunk else sentence
            current_chunk = temp_chunk
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def call_llm(prompt, retry_with_smaller_chunk=None):
    """Call LLM with error handling and automatic retry with smaller chunk."""
    try:
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
    except Exception as e:
        if "413" in str(e) or "too large" in str(e).lower():
            # If we have a smaller chunk to retry with, do that
            if retry_with_smaller_chunk:
                print(f"   ⚠️  Chunk too large, retrying with smaller size...")
                return call_llm(retry_with_smaller_chunk)
            # Otherwise, split the prompt text in half and try again
            prompt_text = prompt.split("Text:\n")[-1] if "Text:\n" in prompt else prompt
            if len(prompt_text) > 5000:  # If still large, split it
                mid_point = len(prompt_text) // 2
                # Try to split at a sentence boundary
                split_point = prompt_text.rfind('.', 0, mid_point)
                if split_point == -1:
                    split_point = prompt_text.rfind('\n', 0, mid_point)
                if split_point == -1:
                    split_point = mid_point
                
                smaller_text = prompt_text[:split_point + 1]
                smaller_prompt = f"""{prompt.split('Text:')[0]}Text:
{smaller_text}
"""
                print(f"   ⚠️  Chunk too large, splitting and retrying...")
                return call_llm(smaller_prompt)
            raise ValueError(f"Text chunk is still too large even after splitting. Error: {e}")
        raise


def extract_json_from_response(response_text):
    """Extract JSON from LLM response, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # If no match, return as-is and let json.loads handle it
    return response_text

def build_final_json(all_chunks_data):
    """Transform chunks into the required schema format."""
    document_id = os.path.splitext(os.path.basename(PDF_FILE))[0]
    
    # Combine all chunks from LLM responses
    all_chunks = []
    chunk_counter = 1
    
    for chunk_data in all_chunks_data:
        try:
            json_str = extract_json_from_response(chunk_data)
            extracted = json.loads(json_str)
            chunks = extracted.get("chunks", [])
            
            # Ensure chunk_ids are unique and sequential
            for chunk in chunks:
                if "chunk_id" not in chunk or not chunk["chunk_id"]:
                    chunk["chunk_id"] = f"{document_id}_chunk_{chunk_counter}"
                chunk_counter += 1
            
            all_chunks.extend(chunks)
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Failed to parse JSON from chunk: {e}")
            print(f"   Response preview: {chunk_data[:200]}...")
            continue
    
    # Group chunks by topic to create topics
    topics_dict = {}
    
    for chunk in all_chunks:
        topic_name = chunk.get("topic", "Unknown Topic")
        # Generate topic_id if not provided
        topic_id = chunk.get("topic_id")
        if not topic_id:
            topic_id = topic_name.lower().replace(" ", "_").replace("-", "_").replace(",", "").replace(".", "").replace("'", "")
            # Remove special characters
            topic_id = re.sub(r'[^a-z0-9_]', '', topic_id)
            if not topic_id:
                topic_id = f"topic_{chunk.get('chunk_id', 'unknown')}"
        
        learning_objective = chunk.get("learning_objective", "")
        text = chunk.get("text", "")
        allowed_concepts = chunk.get("allowed_concepts", [])
        disallowed_concepts = chunk.get("disallowed_concepts", [])
        
        # Ensure arrays are lists
        if not isinstance(allowed_concepts, list):
            allowed_concepts = []
        if not isinstance(disallowed_concepts, list):
            disallowed_concepts = []
        
        # Initialize topic if not exists
        if topic_id not in topics_dict:
            topics_dict[topic_id] = {
                "topic_id": topic_id,
                "topic_name": topic_name,
                "unit": document_id,
                "learning_objectives": [],
                "allowed_concepts": [],
                "disallowed_concepts": [],
                "content_blocks": []
            }
        
        # Add learning objective if not empty and not duplicate
        if learning_objective and learning_objective not in topics_dict[topic_id]["learning_objectives"]:
            topics_dict[topic_id]["learning_objectives"].append(learning_objective)
        
        # Merge allowed/disallowed concepts
        for concept in allowed_concepts:
            if concept and str(concept).strip() and concept not in topics_dict[topic_id]["allowed_concepts"]:
                topics_dict[topic_id]["allowed_concepts"].append(str(concept).strip())
        
        for concept in disallowed_concepts:
            if concept and str(concept).strip() and concept not in topics_dict[topic_id]["disallowed_concepts"]:
                topics_dict[topic_id]["disallowed_concepts"].append(str(concept).strip())
        
        # Add content block
        block_id = chunk.get("chunk_id", f"block_{len(topics_dict[topic_id]['content_blocks']) + 1}")
        # Determine block type based on content
        block_type = "explanation"  # default
        text_lower = text.lower()
        if any(word in text_lower for word in ["example", "for instance", "such as", "e.g."]):
            block_type = "example"
        elif any(word in text_lower for word in ["definition", "defined as", "means", "is"]):
            block_type = "definition"
        
        topics_dict[topic_id]["content_blocks"].append({
            "block_id": block_id,
            "type": block_type,
            "text": text
        })
    
    # Convert to list of topics (schema expects array, but based on error it seems to expect single object)
    # Actually, looking at the schema, it's a single object, not an array
    # But we have multiple topics, so we'll create one topic per document or combine them
    
    # For now, let's create a single topic that combines everything
    # Or we could create multiple topics - let me check the schema again
    # The schema shows it's a single object, so we'll combine all into one topic
    
    if len(topics_dict) == 0:
        # Fallback if no chunks processed
        return {
            "topic_id": document_id,
            "topic_name": document_id,
            "unit": document_id,
            "learning_objectives": [],
            "allowed_concepts": [],
            "disallowed_concepts": [],
            "content_blocks": []
        }
    
    # If multiple topics, combine them into one (or we could return first one)
    # Actually, let's return the first topic or combine all
    if len(topics_dict) == 1:
        return list(topics_dict.values())[0]
    
    # Multiple topics - combine into one
    combined_topic = {
        "topic_id": document_id,
        "topic_name": f"{document_id} - Combined Topics",
        "unit": document_id,
        "learning_objectives": [],
        "allowed_concepts": [],
        "disallowed_concepts": [],
        "content_blocks": []
    }
    
    for topic in topics_dict.values():
        combined_topic["learning_objectives"].extend(topic["learning_objectives"])
        combined_topic["allowed_concepts"].extend(topic["allowed_concepts"])
        combined_topic["disallowed_concepts"].extend(topic["disallowed_concepts"])
        combined_topic["content_blocks"].extend(topic["content_blocks"])
    
    # Remove duplicates
    combined_topic["learning_objectives"] = list(dict.fromkeys(combined_topic["learning_objectives"]))
    combined_topic["allowed_concepts"] = list(dict.fromkeys(combined_topic["allowed_concepts"]))
    combined_topic["disallowed_concepts"] = list(dict.fromkeys(combined_topic["disallowed_concepts"]))
    
    return combined_topic


if __name__ == "__main__":
    text = load_file(TEXT_FILE, PDF_FILE)
    
    print(f"📄 Text length: {len(text)} characters")
    
    # Split text into chunks
    text_chunks = chunk_text(text)
    print(f"📦 Split into {len(text_chunks)} chunks for processing")
    
    base_prompt = """
Rules:
- DO NOT add new information
- DO NOT paraphrase
- ONLY extract curriculum content
- Output JSON with exactly ONE key: "chunks"

Each chunk MUST contain:
- chunk_id (string, unique identifier)
- topic (string, topic name)
- topic_id (string, unique topic identifier, use topic name in lowercase with underscores)
- learning_objective (string, what students should learn)
- text (string, the actual content)
- allowed_concepts (array of strings, mathematical concepts that ARE used/allowed in this content)
- disallowed_concepts (array of strings, mathematical concepts that should NOT be used here, leave empty [] if none)

Example format:
{
  "chunks": [
    {
      "chunk_id": "1",
      "topic": "Patterns in Mathematics",
      "topic_id": "patterns_in_mathematics",
      "learning_objective": "Understanding patterns",
      "text": "Content text here...",
      "allowed_concepts": ["patterns", "sequences", "numbers"],
      "disallowed_concepts": []
    }
  ]
}
"""
    
    all_responses = []
    
    # Process each chunk
    for i, chunk in enumerate(text_chunks, 1):
        chunk_size = len(chunk)
        print(f"🔄 Processing chunk {i}/{len(text_chunks)} ({chunk_size} chars, ~{chunk_size//3.5:.0f} tokens)...")
        
        # If chunk is still too large, split it further
        if chunk_size > MAX_CHARS_PER_CHUNK:
            print(f"   ⚠️  Chunk {i} exceeds limit, splitting further...")
            # Split into smaller sub-chunks
            sub_chunks = chunk_text(chunk, max_chars=MAX_CHARS_PER_CHUNK)
            for j, sub_chunk in enumerate(sub_chunks, 1):
                print(f"   📄 Processing sub-chunk {j}/{len(sub_chunks)} ({len(sub_chunk)} chars)...")
                prompt = f"""{base_prompt}

Text:
{sub_chunk}
"""
                try:
                    raw_output = call_llm(prompt)
                    all_responses.append(raw_output)
                    print(f"      ✅ Sub-chunk {j} processed successfully")
                except Exception as e:
                    print(f"      ❌ Error processing sub-chunk {j}: {e}")
                    raise
        else:
            prompt = f"""{base_prompt}

Text:
{chunk}
"""
            try:
                raw_output = call_llm(prompt)
                all_responses.append(raw_output)
                print(f"   ✅ Chunk {i} processed successfully")
            except Exception as e:
                print(f"   ❌ Error processing chunk {i}: {e}")
                raise
    
    # Combine all chunks
    print("🔗 Combining all chunks...")
    final_json = build_final_json(all_responses)
    
    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2)
    
    print(f"✅ JSON saved to {OUTPUT_FILE}")
    print(f"   Topic ID: {final_json.get('topic_id', 'N/A')}")
    print(f"   Topic Name: {final_json.get('topic_name', 'N/A')}")
    print(f"   Learning Objectives: {len(final_json.get('learning_objectives', []))}")
    print(f"   Content Blocks: {len(final_json.get('content_blocks', []))}")
