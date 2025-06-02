from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.db_conn import get_db
from services.scans.scans import get_scan_history, get_scan_details
from services.auth.auth_service import get_current_user
from services.models import User as UserModel

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("/")
async def list_scans(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns a list of all scans for the current user:
      - scan_id
      - image_url
      - scanned_at
      - final_verdict
    """
    rows = await get_scan_history(db, current_user.user_id)
    return [
        {
            "scan_id": row.scan_id,
            "image_url": row.s3_image_url,
            "scanned_at": row.scanned_at.isoformat(),
            "final_verdict": row.final_verdict.value,
        }
        for row in rows
    ]


@router.get("/{scan_id}")
async def scan_details(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns detailed data for a single scan:
      - scan_id
      - image_url
      - scanned_at
      - final_verdict
      - restrictions (list of names)
      - ingredients (list of { name, verdict, is_trace })
    """
    details = await get_scan_details(db, current_user.user_id, scan_id)
    if not details:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return details
