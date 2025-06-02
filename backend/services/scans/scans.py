from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.models import (
    Scan,
    ScanDietaryRestriction,
    ScanIngredient,
    DietaryRestriction,
    ScanVerdictEnum,
)

async def persist_scan(
    db: AsyncSession,
    user_id: str,
    s3_image_url: str,
    restriction_ids: List[str],
    ingredients: List[Dict[str, Any]],
    traces: List[Dict[str, Any]],
) -> Scan:
    """
    1) Compute the overall final_verdict (ENUM) by looking at ingredient/traces statuses:
       - If any status == 'unsafe'      -> final_verdict = ScanVerdictEnum.unsafe
       - Else if any status == 'potentially unsafe' -> final_verdict = ScanVerdictEnum.potentially_unsafe
       - Else                                -> final_verdict = ScanVerdictEnum.safe
    2) INSERT into scans
    3) INSERT into scan_dietary_restrictions for each restriction_id
    4) INSERT into scan_ingredients for each ingredient (is_trace=False)
    5) INSERT into scan_ingredients for each trace      (is_trace=True)
    6) COMMIT and return the newly created Scan object
    """

    # 1) Compute final_verdict
    all_statuses = [c["status"] for c in ingredients] + [c["status"] for c in traces]
    if "unsafe" in all_statuses:
        final_verdict = ScanVerdictEnum.unsafe
    elif "potentially unsafe" in all_statuses:
        final_verdict = ScanVerdictEnum.potentially_unsafe
    else:
        final_verdict = ScanVerdictEnum.safe

    # 2) Insert into scans
    scan_row = Scan(
        user_id=user_id,
        s3_image_url=s3_image_url,
        final_verdict=final_verdict,
    )
    db.add(scan_row)
    await db.flush()  # so that scan_row.scan_id is populated

    # 3) Insert into scan_dietary_restrictions
    for rid in restriction_ids:
        sd = ScanDietaryRestriction(
            scan_id=scan_row.scan_id, restriction_id=rid
        )
        db.add(sd)

    # 4) Insert main ingredients (is_trace=False)
    for c in ingredients:
        si = ScanIngredient(
            scan_id=scan_row.scan_id,
            ingredient_name=c["ingredient"],
            verdict=c["status"],
            is_trace=False,
        )
        db.add(si)

    # 5) Insert trace ingredients (is_trace=True)
    for c in traces:
        si = ScanIngredient(
            scan_id=scan_row.scan_id,
            ingredient_name=c["ingredient"],
            verdict=c["status"],
            is_trace=True,
        )
        db.add(si)

    # 6) Commit and return
    await db.commit()
    return scan_row


async def get_scan_history(db: AsyncSession, user_id: str) -> List[Any]:
    """
    Returns a list of rows with:
      (scan_id, s3_image_url, scanned_at, final_verdict)
    for all scans belonging to this user_id, ordered by scanned_at DESC.
    """
    result = await db.execute(
        select(
            Scan.scan_id,
            Scan.s3_image_url,
            Scan.scanned_at,
            Scan.final_verdict,
        )
        .where(Scan.user_id == user_id)
        .order_by(Scan.scanned_at.desc())
    )
    return result.all()  # each row is a tuple: (scan_id, s3_image_url, scanned_at, final_verdict)


async def get_scan_details(
    db: AsyncSession, user_id: str, scan_id: str
) -> Dict[str, Any] | None:
    """
    1) Fetch the Scan row
    2) Verify it belongs to this user_id
    3) Fetch all applied restrictions (names) via join on scan_dietary_restrictions
    4) Fetch all ingredients and verdicts from scan_ingredients
    5) Return a dictionary with all relevant fields, or None if scan not found / not owned by user
    """
    # 1) & 2) Fetch scan and verify ownership
    scan_row = await db.get(Scan, scan_id)
    if not scan_row or scan_row.user_id != user_id:
        return None

    # 3) Fetch restriction names
    res = await db.execute(
        select(DietaryRestriction.name)
        .join(
            ScanDietaryRestriction,
            DietaryRestriction.restriction_id == ScanDietaryRestriction.restriction_id,
        )
        .where(ScanDietaryRestriction.scan_id == scan_id)
    )
    restriction_names = [row[0] for row in res.all()]

    # 4) Fetch ingredients + verdicts
    ing_res = await db.execute(
        select(
            ScanIngredient.ingredient_name,
            ScanIngredient.verdict,
            ScanIngredient.is_trace,
        ).where(ScanIngredient.scan_id == scan_id)
    )
    ing_rows = ing_res.all()  # list of (ingredient_name, verdict, is_trace)

    return {
        "scan_id": scan_row.scan_id,
        "image_url": scan_row.s3_image_url,
        "scanned_at": scan_row.scanned_at.isoformat(),
        "final_verdict": scan_row.final_verdict.value,
        "restrictions": restriction_names,
        "ingredients": [
            {
                "name": ing.ingredient_name,
                "verdict": ing.verdict.value,
                "is_trace": ing.is_trace,
            }
            for ing in ing_rows
        ],
    }
