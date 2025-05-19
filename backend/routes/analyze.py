from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool
from typing import List, Union

from services.analyze.upload.upload_service import UploadService
from services.analyze.process.ocr_service import OCRService
from services.analyze.process.classification_service import ClassificationService

import traceback

router = APIRouter(prefix="/analyze", tags=["analyze"])

upload_service = UploadService()
ocr_service = OCRService()
classification_service = ClassificationService()

# Request models
class UploadRequest(BaseModel):
    image_base64: str

class AnalyzeRequest(BaseModel):
    s3_key: str
    restriction: Union[str, List[str]]

@router.post("/upload")
async def upload_image(data: UploadRequest):
    try:
        image_key = await run_in_threadpool(upload_service.upload_base64_image, data.image_base64)
        return {"s3_key": image_key}
    except Exception as e:
        print(f"[ERROR] /analyze/upload: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to upload image.")

@router.post("/process")
async def analyze_image(data: AnalyzeRequest):
    try:
        parsed = await run_in_threadpool(ocr_service.extract_ingredients_from_s3, data.s3_key)

        ingredients = parsed["ingredients"]
        traces = parsed["traces"]

        classified_ingredients = await run_in_threadpool(classification_service.classify_ingredients, ingredients, data.restriction)
        classified_traces = await run_in_threadpool(classification_service.classify_ingredients, traces, data.restriction)

        result = {
            "ingredients": {c["ingredient"]: {"status": c["status"]} for c in classified_ingredients},
            "traces": {c["ingredient"]: {"status": c["status"]} for c in classified_traces}
        }

        return {
            "s3_key": data.s3_key,
            "classified": result
        }
    
    except Exception as e:
        print(f"[ERROR] /analyze/process: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to analyze image.")
