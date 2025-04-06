from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.textract_pipeline import TextractProcessor
from services.ingredient_classifier import IngredientClassifier
from fastapi.concurrency import run_in_threadpool
import traceback

router = APIRouter()

class UploadRequest(BaseModel):
    image_base64: str
    restriction: str

@router.post("/analyze")
async def analyze_product(data: UploadRequest):
    try:
        processor = TextractProcessor()
        classifier = IngredientClassifier()

        s3_key = await run_in_threadpool(processor.save_image_to_s3, data.image_base64)
        extracted_text = await run_in_threadpool(processor.extract_text, s3_key)
        classified = await run_in_threadpool(classifier.classify, extracted_text, data.restriction)

        return {
            "s3_key": s3_key,
            "text": extracted_text,
            "classified": classified
        }

    except Exception as e:
        print(f"[ERROR] /analyze: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))