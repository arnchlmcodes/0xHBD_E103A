
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
CONTENT_DIR = BASE_DIR / "content"  # NEW ROOT
OUTPUT_DIR = BASE_DIR / "generated_content"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)  # Ensure content dir exists
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

class FileInfo(BaseModel):
    filename: str
    display_name: str
    topics: List[str]
    topic_count: int

class FolderInfo(BaseModel):
    folder: str
    files: List[FileInfo]

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"status": "System Online", "message": "Teaching Assistant API is running"}

@app.get("/files", response_model=List[FolderInfo])
async def list_files():
    """List all processed JSON files recursively from content directory"""
    results = []
    if not CONTENT_DIR.exists():
        return []

    # Iterate over directories in content (e.g., class7, class8)
    for folder_path in CONTENT_DIR.iterdir():
        if folder_path.is_dir():
            folder_name = folder_path.name
            files_list = []
            
            # Recursively find .json files inside this folder
            for f in folder_path.rglob("*.json"):
                # FILTER: Skip backend mapping files
                if f.name.startswith("chapter_mapping"):
                    continue

                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        if isinstance(data, dict):
                            data = [data]
                        
                        topics = [item.get('topic_name', 'Unknown') for item in data]
                        
                        # LOGIC: Use first topic as the main display name, fallback to filename
                        if topics and topics[0] != 'Unknown':
                            display_name = topics[0]
                        else:
                            display_name = f.stem.replace('_', ' ').title()

                        # Create relative path from CONTENT_DIR
                        rel_path = f.relative_to(CONTENT_DIR)
                        
                        files_list.append({
                            "filename": str(rel_path).replace("\\", "/"), # normalized path
                            "display_name": display_name,
                            "topics": topics,
                            "topic_count": len(topics)
                        })
                except Exception:
                    files_list.append({
                        "filename": str(f.relative_to(CONTENT_DIR)), 
                        "display_name": f.stem, 
                        "topics": ["Error reading file"], 
                        "topic_count": 0
                    })
            
            if files_list:
                results.append({
                    "folder": folder_name,
                    "files": files_list
                })
            
    return results

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF and process it immediately"""
    # ... logic remains same, but maybe default upload location logic needs revisit?
    # Keeping upload simple for now, as user request focused on VIEWING specific folders.
    file_path = UPLOAD_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        schema_path = BASE_DIR / "curriculum_schema.json"
        
        from extract_pipeline import process_specific_pdf, load_schema
        
        schema = load_schema()
        if not schema:
            return JSONResponse(status_code=500, content={"error": "Schema not found"})
            
        # define custom dir
        CUSTOM_DIR = CONTENT_DIR / "custom"
        CUSTOM_DIR.mkdir(parents=True, exist_ok=True)

        json_output = process_specific_pdf(file_path, schema, custom_output_base=CUSTOM_DIR)
        
        if json_output:
            # We need to tell frontend where it went. process_specific_pdf defaults to class7/json_output usually?
            # For now return name. Frontend refresh will catch it if it went to content/class7
            return {"status": "success", "message": "File processed", "json_file": json_output.name}
        else:
            return JSONResponse(status_code=500, content={"error": "Processing failed"})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Helper to resolve path
def get_json_path(filename: str) -> Path:
    # filename includes folder relative to content dir (e.g. class7/json_output/abc.json)
    return CONTENT_DIR / filename

@app.post("/generate/plan")
async def generate_plan(request: GenerateRequest):
    """Generate Teaching Plan PDF"""
    json_path = get_json_path(request.filename)
    if not json_path.exists():
        # Fallback for legacy calls (flat filename)
        # Search recursively? No, let's enforce path.
        raise HTTPException(status_code=404, detail=f"File not found at {json_path}")
        
    output_filename = f"Plan_{json_path.stem}_{request.topic_index}.pdf"
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
    json_path = get_json_path(request.filename)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    output_filename = f"Quiz_{json_path.stem}_{request.topic_index}.pdf"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        result = run_quiz_generator(str(json_path), str(output_path), request.topic_index)
        # Assuming run_quiz_generator returns a dict with 'data' key as per my previous update to generate_quiz.py
        # If it returns just path (old version), I need to be careful. 
        # Checking generate_quiz.py: It returns { "pdf_path": ..., "json_path": ..., "data": ... }
        
        return {
            "status": "success", 
            "file_url": f"/download/{output_filename}", 
            "filename": output_filename,
            "data": result['data'] 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/flashcards")
async def generate_flashcards(request: GenerateRequest):
    """Generate Flashcards JSON"""
    json_path = get_json_path(request.filename)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    output_filename = f"Flashcards_{json_path.stem}_{request.topic_index}.json"
    output_path = OUTPUT_DIR / output_filename
    
    try:
        final_path = run_flashcard_generator(str(json_path), str(output_path), request.topic_index)
        
        with open(final_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            
        return {"status": "success", "data": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/practice")
async def generate_practice(request: GenerateRequest):
    """Generate Practice Questions PDF"""
    json_path = get_json_path(request.filename)
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            data = [data]
            
        target_data = [data[request.topic_index]]
        
        from practice_questions import generate_questions_from_json, create_pdf
        
        output_filename = f"Practice_{json_path.stem}_{request.topic_index}.pdf"
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
    if "error" in response:
        # FIX: Return error as a chat message so frontend can display it
        # raise HTTPException(status_code=500, detail=response["error"])
        return {
            "answer": f"⚠️ Chatbot Error: {response['error']}",
            "chapter": "System Error",
            "relevance": 0,
            "sources": []
        }
        
    return response

@app.post("/generate/video")
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate Shortform Video (Background Task) with Unique Filename"""
    json_path = get_json_path(request.filename)
    
    with open("debug_log.txt", "a") as log:
        log.write(f"\n--- Video Gen Request ---\n")
        log.write(f"Requested Filename: {request.filename}\n")
        log.write(f"Resolved Path: {json_path}\n")
        log.write(f"Exists: {json_path.exists()}\n")
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found at {json_path}")
        
    # UNIQUE FILENAME LOGIC
    import uuid
    import time
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:6]
    output_filename = f"Video_{json_path.stem}_{request.topic_index}_{timestamp}_{unique_id}.mp4"
    output_path = OUTPUT_DIR / output_filename
    
    # Define the background task wrapper
    def _run_gen():
        try:
            with open("debug_log.txt", "a") as log:
                log.write(f"Starting run_video_generator -> {output_filename}\n")
                
            # PASS unique filename to generator
            run_video_generator(str(json_path), str(OUTPUT_DIR), request.topic_index, custom_filename=output_filename)
            
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
        "filename": output_filename, # Frontend polls this UNIQUE key
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
