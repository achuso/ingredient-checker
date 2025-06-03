from fastapi import APIRouter, Depends, HTTPException

from services.scans.scans import get_scan_history, get_scan_details
from services.auth.auth_service import get_current_user
from services.models import User as UserModel

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", summary="List scans for current user")
async def list_scans(current_user: UserModel = Depends(get_current_user)):
    return await get_scan_history(str(current_user.user_id))


@router.get("/{scan_id}", summary="Get single-scan detail")
async def scan_detail(scan_id: str, current_user: UserModel = Depends(get_current_user)):
    try:
        return await get_scan_details(str(current_user.user_id), scan_id)
    except HTTPException:
        raise 
