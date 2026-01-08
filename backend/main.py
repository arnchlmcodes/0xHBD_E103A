
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import shutil
import os
import sys
import json
from pathlib import Path
from typing import List, Optional
import uuid

# Add parent directory to sys.path to import sibling scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import existing core modules
# Note: We need to handle potential import errors if dependencies are missing
try:
    from extract_pipeline import process_single_file, validate_json_file
    from generate_plan import run_teaching_plan_generator
    from generate_quiz import run_quiz_generator
    from generate_flashcards import run_flashcard_generator
    from practice_questions import generate_questions_from_json, create_pdf
    from generate_animations_synchronized import run_video_generator
    from chatbot_rag import MathBuddyChatbot
except ImportError as e:
    print(f"Server Startup Error: Could not import modules. {e}")
    # We continue so we can at least show errors via API
    pass

app = FastAPI(title="Teaching Assistant API", version="1.0.0")

# CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_JSON_DIR = BASE_DIR / "class7" / "json_output"
OUTPUT_DIR = BASE_DIR / "generated_content"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_JSON_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Chatbot
chatbot_instance = None
try:
    # Check if we are in the correct directory for relative paths in chatbot
    # chatbot_rag expects chapter_mapping_class7.json in CWD
    # We might need to change CWD or pass path needed. 
    # For now, let's assume server is run from root.
    chatbot_instance = MathBuddyChatbot()
except Exception as e:
    print(f"⚠️ Chatbot initialization failed: {e}")

class ChatRequest(BaseModel):
    message: str

class GenerateRequest(BaseModel):
    filename: str
    topic_index: int = 0

class ChapterInfo(BaseModel):
    filename: str
    topics: List[str]
    topic_count: int

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"status": "System Online", "message": "Teaching Assistant API is running"}

@app.get("/files", response_model=List[ChapterInfo])
async def list_files():
    """List all processed JSON files and their topics"""
    results = []
    if not PROCESSED_JSON_DIR.exists():
        return []
        
    for f in PROCESSED_JSON_DIR.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    data = [data]
                
                topics = [item.get('topic_name', 'Unknown') for item in data]
                results.append({
                    "filename": f.name,
                    "topics": topics,
                    "topic_count": len(topics)
                })
        except Exception:
            results.append({"filename": f.name, "topics": ["Error reading file"], "topic_count": 0})
            
    return results

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF and process it immediately"""
    file_path = UPLOAD_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Trigger processing
    # For MVP, we run synchronously to return status, or use background tasks
    # Using background task is better for UI responsiveness, but user wants immediate feedback?
    # Let's run synchronously for simplicity of "Phase 3: Generation & Loading" flow
    
    try:
        # We need to use the schema from the root dir
        schema_path = BASE_DIR / "curriculum_schema.json"
        
        # Call extract_pipeline logic
        # process_single_file returns the output JSON path
        # process_single_file expects a text file path usually, OR we can use process_specific_pdf logic 
        # But process_specific_pdf is not imported. Let's rely on process_single_file from text?
        # Actually extract_pipeline.py has `process_specific_pdf`. Let's assume we can import it or reimplement.
        
        # Since I can't easily import `process_specific_pdf` because it wasn't in the top level defs I checked carefully...
        # Wait, I saw `process_specific_pdf` in `extract_pipeline.py` earlier.
        # I need to make sure I import it.
        from extract_pipeline import process_specific_pdf, load_schema
        
        schema = load_schema()
        if not schema:
            return JSONResponse(status_code=500, content={"error": "Schema not found"})
            
        json_output = process_specific_pdf(file_path, schema)
        
        if json_output:
            return {"status": "success", "message": "File processed", "json_file": json_output.name}
        else:
            return JSONResponse(status_code=500, content={"error": "Processing failed"})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/generate/plan")
async def generate_plan(request: GenerateRequest):
    """Generate Teaching Plan PDF"""
    json_path = PROCESSED_JSON_DIR / request.filename
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    output_filename = f"Plan_{request.filename.replace('.json', '')}_{request.topic_index}.pdf"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        final_path = run_teaching_plan_generator(str(json_path), str(output_path), request.topic_index)
        if final_path:
            return {"status": "success", "file_url": f"/download/{output_filename}", "filename": output_filename}
        else:
            raise HTTPException(status_code=500, detail="Generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/quiz")
async def generate_quiz(request: GenerateRequest):
    """Generate Quiz PDF"""
    json_path = PROCESSED_JSON_DIR / request.filename
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    output_filename = f"Quiz_{request.filename.replace('.json', '')}_{request.topic_index}.pdf"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        final_path = run_quiz_generator(str(json_path), str(output_path), request.topic_index)
        return {"status": "success", "file_url": f"/download/{output_filename}", "filename": output_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/flashcards")
async def generate_flashcards(request: GenerateRequest):
    """Generate Flashcards JSON"""
    json_path = PROCESSED_JSON_DIR / request.filename
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    output_filename = f"Flashcards_{request.filename.replace('.json', '')}_{request.topic_index}.json"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        final_path = run_flashcard_generator(str(json_path), str(output_path), request.topic_index)
        
        # Load content to return to frontend for display
        with open(final_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            
        return {"status": "success", "data": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/practice")
async def generate_practice(request: GenerateRequest):
    """Generate Practice Questions PDF (Section A/B/C)"""
    json_path = PROCESSED_JSON_DIR / request.filename
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load JSON data
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Normalize
        if isinstance(data, dict):
            data = [data]
            
        # Filter for specific topic if needed, or send all? 
        # process_questions usually handles the whole file. 
        # Let's slice the data to just the requested topic for specificity?
        # practice_questions.py logic handles valid JSON structure.
        
        target_data = [data[request.topic_index]]
        
        # Call generation (using the logic from practice_questions.py)
        # We need to import the logic.
        from practice_questions import generate_questions_from_json, create_pdf
        
        output_filename = f"Practice_{request.filename.replace('.json', '')}_{request.topic_index}.pdf"
        output_path = OUTPUT_DIR / output_filename
        
        questions = generate_questions_from_json(target_data, request.filename)
        success = create_pdf(questions, output_path)
        
        if success:
            return {"status": "success", "file_url": f"/download/{output_filename}", "filename": output_filename}
        else:
            raise HTTPException(status_code=500, detail="PDF Creation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """RAG Chatbot Endpoint"""
    if not chatbot_instance:
        return {"answer": "Chatbot is offline (Check API Keys or Init).", "chapter": "System", "relevance": 0}
    
    response = chatbot_instance.get_response(request.message)
    # The chatbot returns a dict with answer, chapter, etc. or error
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
        
    return response

@app.post("/generate/video")
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate Shortform Video (Background Task)"""
    json_path = PROCESSED_JSON_DIR / request.filename
    
    # LOGGING TO FILE
    with open("debug_log.txt", "a") as log:
        log.write(f"\n--- Video Gen Request ---\n")
        log.write(f"Requested Filename: {request.filename}\n")
        log.write(f"Resolved Path: {json_path}\n")
        log.write(f"Exists: {json_path.exists()}\n")
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found at {json_path}")
        
    # We use a deterministic filename so frontend can poll for it
    output_filename = f"Video_{request.filename.replace('.json', '')}_{request.topic_index}.mp4"
    output_path = OUTPUT_DIR / output_filename
    
    # Cleanup existing file to prevent instant-poll of old file
    if output_path.exists():
        try:
            os.remove(output_path)
            with open("debug_log.txt", "a") as log:
                log.write(f"Deleted old output file: {output_path}\n")
        except Exception as e:
            with open("debug_log.txt", "a") as log:
                log.write(f"Failed to delete old file: {e}\n")
    
    # Define the background task wrapper
    def _run_gen():
        try:
            with open("debug_log.txt", "a") as log:
                log.write("Starting run_video_generator...\n")
            run_video_generator(str(json_path), str(OUTPUT_DIR), request.topic_index)
            with open("debug_log.txt", "a") as log:
                log.write("Finished run_video_generator.\n")
        except Exception as e:
            print(f"Background Video Gen Failed: {e}")
            with open("debug_log.txt", "a") as log:
                log.write(f"Background Video Gen Failed: {e}\n")

    background_tasks.add_task(_run_gen)
    
    return {
        "status": "processing", 
        "message": "Video generation started in background", 
        "filename": output_filename,
        "check_url": f"/download/{output_filename}"
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Backend Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
