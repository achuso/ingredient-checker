from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.textract_pipeline import TextractProcessor
import traceback

router = APIRouter()

class UploadRequest(BaseModel):
    image_base64: str

@router.post("/analyze")
def analyze_product(data: UploadRequest):
    try:
        processor = TextractProcessor()
        s3_key = processor.save_image_to_s3(data.image_base64)
        extracted_text = processor.extract_text(s3_key)

        return {
            "s3_key": s3_key,
            "text": extracted_text
        }

    except Exception as e:
        print(f"[ERROR] /upload: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
