from __future__ import annotations

import logging
from typing import List, Literal, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from services.analyze.upload.upload_service import UploadService
from services.analyze.process.ocr_service import OCRService
from services.analyze.process.classification_service import ClassificationService
from services.analyze.process.llm_service import LLMService
from services.scans.scans import persist_scan
from services.db_conn import get_db
from services.auth.auth_service import get_current_user
from services.models import User as UserModel

router = APIRouter(prefix="/analyze", tags=["analyze"])
logger = logging.getLogger(__name__)

_upload = UploadService()
_ocr = OCRService()
_rules = ClassificationService()
_llm = LLMService()


#  Pydantic 
class AnalyzeRequest(BaseModel):
    image_base64: str
    restriction_ids: List[str]
    method: Literal["rule", "llm"] = Field(
        "rule", description="Processing engine to use"
    )


# helpers & normalisation
def _normalise(raw: Any) -> List[Dict[str, str]]:
    """
    Make *anything* (dict, list, plain string) look like:
    [{'ingredient': str, 'status': str}, …]
    """
    out: List[Dict[str, str]] = []

    if raw is None:
        return out

    if isinstance(raw, list):
        for item in raw:
            out.extend(_normalise(item))
        return out

    # dict mapping ingredient to status
    if isinstance(raw, dict) and all(isinstance(k, str) for k in raw):
        for k, v in raw.items():
            status = (
                v.get("status")
                if isinstance(v, dict)
                else (v if isinstance(v, str) else "unknown")
            )
            out.append({"ingredient": k, "status": status})
        return out

    # single dict describing an entry
    if isinstance(raw, dict):
        name = (
            raw.get("ingredient")
            or raw.get("name")
            or raw.get("key")
            or str(raw)
        )
        status = raw.get("status") or raw.get("verdict") or raw.get("value") or "unknown"
        return [{"ingredient": str(name), "status": str(status)}]

    # plain string (or anything else)
    return [{"ingredient": str(raw), "status": "unknown"}]


def _compute_final_verdict(
    cls_ing: List[Dict[str, Any]], cls_tr: List[Dict[str, Any]]
) -> str:
    priority = {
        "definitely unsafe": 4,
        "unsafe": 3,
        "maybe unsafe": 2,
        "potentially unsafe": 2,
        "safe": 1,
    }

    def _score(item: Dict[str, Any]) -> int:
        return priority.get(str(item.get("status", "")).lower(), 0)

    scores = [_score(i) for i in cls_ing] + [_score(t) for t in cls_tr]
    if not scores:
        return "unknown"
    worst = max(scores)
    for k, v in priority.items():
        if v == worst:
            return k
    return "unknown"


# endpoint
@router.post("/process")
async def process_scan(
    data: AnalyzeRequest,
    db=Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    # 1) upload to S3
    try:
        s3_key = await run_in_threadpool(
            _upload.upload_base64_image, data.image_base64
        )
    except Exception as e:
        logger.error("upload failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload image.")

    # 2) classify
    restrictions = data.restriction_ids or []

    try:
        if data.method == "llm":
            # OCR → LLM
            raw_text = await run_in_threadpool(_ocr.extract_text, s3_key)
            out: Dict[str, Any] = await run_in_threadpool(
                _llm.classify_from_ocr_text, raw_text, restrictions
            )

            cls_ing = _normalise(out.get("ingredients"))
            cls_tr = _normalise(out.get("traces"))

        else:  # rule-based
            parsed = await run_in_threadpool(
                _ocr.extract_ingredients_from_s3, s3_key
            )
            # parsed["ingredients"] and ["traces"] are lists[str]
            cls_ing = await run_in_threadpool(
                _rules.classify_ingredients, parsed["ingredients"], restrictions
            )
            cls_tr = await run_in_threadpool(
                _rules.classify_ingredients, parsed["traces"], restrictions
            )

    except Exception as e:
        logger.error("classification failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to classify image.")

    # 3) compute verdict & DB persist
    verdict = _compute_final_verdict(cls_ing, cls_tr)

    merged = (
        [
            {
                "ingredient": c["ingredient"],
                "verdict": c["status"],
                "is_trace": False,
            }
            for c in cls_ing
        ]
        + [
            {
                "ingredient": c["ingredient"],
                "verdict": c["status"],
                "is_trace": True,
            }
            for c in cls_tr
        ]
    )

    try:
        row = await persist_scan(
            user_id=str(current_user.user_id),
            s3_image_url=s3_key,
            final_verdict=verdict,
            restriction_ids=restrictions,
            ingredients=merged,
        )
    except Exception as e:
        logger.error("DB persistence failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save scan.")

    # 4) respond in the same shape the frontend already consumes
    classified_payload = {
        "ingredients": {
            c["ingredient"]: {"status": c["status"]} for c in cls_ing
        },
        "traces": {c["ingredient"]: {"status": c["status"]} for c in cls_tr},
    }

    return {
        "scan_id": row["scan_id"],
        "s3_image_url": row["s3_image_url"],
        "final_verdict": row["final_verdict"],
        "classified": classified_payload,
    }
