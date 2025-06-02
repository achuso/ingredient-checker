from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Dict
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from services.analyze.upload.upload_service import UploadService
from services.analyze.process.ocr_service import OCRService
from services.analyze.process.classification_service import ClassificationService
from services.analyze.process.llm_service import LLMService

from services.db_conn import get_db
from services.scans.scans import persist_scan
from services.auth.auth_service import get_current_user
from services.models import ScanVerdictEnum, User as UserModel

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = logging.getLogger(__name__)

# Singletons for upload/OCR/classification
_upload = UploadService()
_ocr = OCRService()
_rules = ClassificationService()
_llm = LLMService()


class AnalyzeRequest(BaseModel):
    image_base64: str
    restriction_ids: List[str]
    method: Literal["rule", "llm"] = Field(
        "rule", description="Processing engine to use"
    )


@router.post("/process")
async def process_scan(
    data: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    1) Uploads the base64 image to S3
    2) Runs OCR + rule-based or LLM-based classification
    3) Persists the new scan into the database (scans, scan_dietary_restrictions, scan_ingredients)
    4) Returns scan_id, s3_image_url, final_verdict, and the raw classification result
    """

    # ---- 1) Upload image to S3 ----
    try:
        s3_key = await run_in_threadpool(_upload.upload_base64_image, data.image_base64)
    except Exception as e:
        logger.error("upload failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image.")

    # ---- 2) Run classification ----
    restrictions = data.restriction_ids
    try:
        if data.method == "llm":
            raw_text = await run_in_threadpool(_ocr.extract_text, s3_key)
            classified_dict: Dict = await run_in_threadpool(
                _llm.classify_from_ocr_text, raw_text, restrictions
            )

            # Expecting LLMService to return something like:
            #    { "ingredients": [{"ingredient": "...", "status": "safe"}, ...],
            #      "traces":      [{"ingredient": "...", "status": "potentially unsafe"}, ...] }
            cls_ing = classified_dict.get("ingredients", [])
            cls_tr = classified_dict.get("traces", [])

        else:
            parsed = await run_in_threadpool(_ocr.extract_ingredients_from_s3, s3_key)
            cls_ing = await run_in_threadpool(
                _rules.classify_ingredients, parsed["ingredients"], restrictions
            )
            cls_tr = await run_in_threadpool(
                _rules.classify_ingredients, parsed["traces"], restrictions
            )

    except Exception as e:
        logger.error("classification failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to classify image.")

    # ---- 3) Persist into the database ----
    try:
        new_scan = await persist_scan(
            db=db,
            user_id=current_user.user_id,
            s3_image_url=s3_key,
            restriction_ids=restrictions,
            ingredients=cls_ing,
            traces=cls_tr,
        )
    except Exception as e:
        logger.error("DB persistence failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save scan.")

    # ---- 4) Return the response ----
    return {
        "scan_id": new_scan.scan_id,
        "s3_image_url": new_scan.s3_image_url,
        "final_verdict": new_scan.final_verdict.value,
        "classified": {
            "ingredients": {c["ingredient"]: {"status": c["status"]} for c in cls_ing},
            "traces": {c["ingredient"]: {"status": c["status"]} for c in cls_tr},
        },
    }
