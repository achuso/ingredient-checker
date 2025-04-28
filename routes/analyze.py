from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool

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
    restriction: str

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
        ingredients = await run_in_threadpool(ocr_service.extract_ingredients_from_s3, data.s3_key)
        classified = await run_in_threadpool(classification_service.classify_ingredients, ingredients, data.restriction)

        return {
            "s3_key": data.s3_key,
            "ingredients": ingredients,
            "classified": classified
        }
    
    except Exception as e:
        print(f"[ERROR] /analyze/process: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to analyze image.")
