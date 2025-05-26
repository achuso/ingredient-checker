from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from typing import List, Union, Literal, Dict
import logging

from services.analyze.upload.upload_service import UploadService
from services.analyze.process.ocr_service import OCRService
from services.analyze.process.classification_service import ClassificationService
from services.analyze.process.llm_service import LLMService

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = logging.getLogger(__name__)

# singletons
_upload  = UploadService()
_ocr     = OCRService()
_rules   = ClassificationService()
_llm     = LLMService()

class UploadRequest(BaseModel):
    image_base64: str

class AnalyzeRequest(BaseModel):
    s3_key: str
    restriction: Union[str, List[str]]
    method: Literal["rule", "llm"] = Field("rule", description="Processing engine to use")

# routes
@router.post("/upload")
async def upload_image(data: UploadRequest):
    try:
        key = await run_in_threadpool(_upload.upload_base64_image, data.image_base64)
        return {"s3_key": key}
    except Exception as e:
        logger.error("upload_image failed: %s", e, exc_info=True)
        raise HTTPException(500, "Failed to upload image.")


@router.post("/process")
async def process_image(data: AnalyzeRequest):
    restrictions = [data.restriction] if isinstance(data.restriction, str) else data.restriction

    #  LLM‑based alternative
    if data.method == "llm":
        try:
            raw_text = await run_in_threadpool(_ocr.extract_text, data.s3_key)
            llm_result: Dict = await run_in_threadpool(_llm.classify_from_ocr_text, raw_text, restrictions)
            return {"s3_key": data.s3_key, "classified": llm_result}
        except Exception as e:
            logger.error("Bedrock LLM failed: %s", e, exc_info=True)
            raise HTTPException(502, "LLM processing failed.")

    # deterministic pipeline
    try:
        parsed = await run_in_threadpool(_ocr.extract_ingredients_from_s3, data.s3_key)
        ingredients, traces = parsed["ingredients"], parsed["traces"]

        cls_ing = await run_in_threadpool(_rules.classify_ingredients, ingredients, restrictions)
        cls_tr  = await run_in_threadpool(_rules.classify_ingredients, traces, restrictions)

        result = {
            "ingredients": {c["ingredient"]: {"status": c["status"]} for c in cls_ing},
            "traces":      {c["ingredient"]: {"status": c["status"]} for c in cls_tr},
        }
        return {"s3_key": data.s3_key, "classified": result}

    except Exception as e:
        logger.error("rule‑based processing failed: %s", e, exc_info=True)
        raise HTTPException(500, "Failed to analyze image.")
