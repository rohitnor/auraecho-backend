import os
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware 
from models import AnalysisRequest, AnalysisResponse, SearchRequest, SearchResponse
from ai_service import analyze_text_with_llm, search_similar_notes, transcribe_audio_with_groq

app = FastAPI(title="AuraEcho AI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_endpoint(request: AnalysisRequest):
    try:
        result = analyze_text_with_llm(request.raw_text)
        return AnalysisResponse(**result)
    except Exception as e:
        print(f"\n=== !!! TEXT WORKFLOW CRASHED !!! ===\nError: {str(e)}\n===================================\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    try:
        results = search_similar_notes(request.query)
        return SearchResponse(results=results)
    except Exception as e:
        print(f"\n=== !!! SEARCH WORKFLOW CRASHED !!! ===\nError: {str(e)}\n=====================================\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-audio", response_model=AnalysisResponse)
async def analyze_audio_endpoint(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    
    try:
        # 1. Save the incoming audio file locally temporarily
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # 2. Transcribe the audio using Groq Whisper
        transcription_text = transcribe_audio_with_groq(temp_file_path)
        
        # 3. Pass the transcribed text into your exact same RAG pipeline
        result = analyze_text_with_llm(transcription_text)
        
        return AnalysisResponse(**result)
        
    except Exception as e:
        print(f"\n=== !!! AUDIO WORKFLOW CRASHED !!! ===\nError: {str(e)}\n=====================================\n")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # 4. Cleanup: Delete the temp file so your hard drive doesn't fill up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)