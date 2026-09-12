import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from agent.orchestrator import StudyAgentOrchestrator
from agent.syllabus import UNIVERSAL_SUBJECTS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AlexandriaAcademicServer")

app = FastAPI(title="Alexandria Studio • AI Academic & Engineering Study Studio")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent Orchestrator
orchestrator = StudyAgentOrchestrator(
    openrouter_api_key=config.OPENROUTER_API_KEY,
    serper_api_key=config.SERPER_API_KEY,
    model=config.OPENROUTER_MODEL,
    output_dir=config.OUTPUT_DIR
)

# Ensure directories exist
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

def _load_history() -> list[dict]:
    if config.LIBRARY_HISTORY_FILE.exists():
        try:
            with open(config.LIBRARY_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading history: {e}")
    return []

def _save_history(item: dict):
    history = _load_history()
    # Avoid duplicate IDs
    history = [h for h in history if h.get("id") != item.get("id")]
    history.insert(0, item)
    # Keep up to 30 past books
    history = history[:30]
    try:
        with open(config.LIBRARY_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving history: {e}")

class GenerateRequest(BaseModel):
    topic: str
    model: str = "google/gemini-3.8-flash"
    subject: str = ""
    formats: list[str] = ["handwritten", "pdf"]

@app.api_route("/", methods=["GET", "HEAD"])
def serve_index():
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index HTML not found")
    return FileResponse(str(index_path))

@app.get("/api/health")
def health_check():
    valid, missing = config.validate_keys()
    return {
        "status": "healthy" if valid else "missing_keys",
        "missing_keys": missing,
        "default_model": config.OPENROUTER_MODEL
    }

@app.get("/api/subjects")
def get_subjects():
    """Return universal academic subjects & authoritative reference textbooks."""
    return UNIVERSAL_SUBJECTS

@app.get("/api/usage")
def get_token_usage():
    """Return live token consumption, quota percentage, and model health."""
    usage_data = orchestrator.tracker.to_dict()
    # Add metadata for UI display
    usage_data["default_model"] = orchestrator.default_model
    usage_data["free_fallback"] = "nvidia/nemotron-3.5-lightning:free"
    return usage_data

@app.post("/api/usage/reset")
def reset_token_usage():
    """Reset the session token counter."""
    orchestrator.tracker.reset()
    return {"status": "reset", "usage": orchestrator.tracker.to_dict()}

@app.get("/api/history")
def get_history():
    return _load_history()

@app.delete("/api/history/{book_id}")
def delete_book(book_id: str):
    """Delete a book from the shelf and purge its generated files."""
    history = _load_history()
    target_book = next((b for b in history if b.get("id") == book_id), None)
    
    if not target_book:
        raise HTTPException(status_code=404, detail="Book not found on shelf")

    # Filter out from history
    new_history = [b for b in history if b.get("id") != book_id]
    try:
        with open(config.LIBRARY_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(new_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving updated history: {e}")

    # Delete physical generated files
    files = target_book.get("files", {})
    for fmt, rel_url in files.items():
        if rel_url and rel_url.startswith("/api/download/"):
            fname = rel_url.replace("/api/download/", "")
            fpath = config.OUTPUT_DIR / fname
            if fpath.exists():
                try:
                    fpath.unlink()
                    logger.info(f"Deleted file: {fpath}")
                except Exception as e:
                    logger.warning(f"Could not delete {fpath}: {e}")

    logger.info(f"Book '{target_book.get('topic')}' (ID: {book_id}) deleted from shelf.")
    return {"status": "deleted", "id": book_id}

@app.post("/api/generate")
def generate_study_notes(req: GenerateRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required.")
    
    valid, missing = config.validate_keys()
    if not valid:
        raise HTTPException(
            status_code=500, 
            detail=f"Missing API keys in .env: {', '.join(missing)}"
        )

    try:
        package = orchestrator.generate_study_package(
            query=req.topic,
            gui_model=req.model,
            gui_subject=req.subject,
            requested_formats=req.formats
        )
        _save_history(package)
        return package
    except Exception as e:
        logger.error(f"Error generating study notes for '{req.topic}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/download/{filename}", methods=["GET", "HEAD"])
def download_file(filename: str):
    file_path = config.OUTPUT_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Secure against directory traversal
    if not file_path.resolve().is_relative_to(config.OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Forbidden")

    ext = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 65)
    print(f"🏛️ ALEXANDRIA Studio launching on http://localhost:{config.PORT}")
    print("=" * 65 + "\n")
    uvicorn.run("server:app", host=config.HOST, port=config.PORT, reload=True)
