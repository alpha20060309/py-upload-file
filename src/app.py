from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from src.validators import DocumentValidator

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="FastAPI File Upload Service")

doc_validator = DocumentValidator(max_size=25 * 1024 * 1024)

@app.post("/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload multiple files with validation"""

    if len(files)>10:
        raise HTTPException(status_code=400, detail = "Too many files. Maximum 10 files allowed")

    results = []

    for file in files:
        validation = await doc_validator.validate_file(file)

        if not validation["valid"]:
            results.append({
                "filename": file.filename,
                "success": false,
                "errors": validation["errors"]
            })
            continue

        # Save valid files
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file,buffer)

            results.append({
                "success": True,
                "filename": file.filename,
                "stored_filename": unique_filename,
                "location": str(file_path)
            })
        except Exception as e:
            results.append({
                "sucess": False,
                "filename": file.filename,
                "errors": [f"Failed to save: {str(e)}"]
            })

    sucessful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    return {
        "total_files": len(files),
        "successful": len(sucessful),
        "failed": len(failed),
        "upload_time": datetime.utcnow().isoformat(),
        "results" : results
    }

@app.post("/upload/single")
async def upload_single_file(file: UploadFile=File(...)):
    """Upload a single file with basic validation"""

    # Validate file first
    validation = await doc_validator.validate_file(file)

    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={"message": "File validation failed", "errors":validation["errors"]})

    # Create unique filename to prevent conflicts
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to save file: {str(e)}")

    return{
        "success": True,
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "file_size": file.size,
        "upload_time": datetime.utcnow().isoformat(),
        "location": str(file_path)
    }

@app.get("/")
async def root():
    return {"message": "FastAPI File Upload Service is running"}