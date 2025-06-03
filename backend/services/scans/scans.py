"""services/scans/scans.py – unified persistence helpers (async/asyncpg)
Fixed syntax error (extra comma + parenthesis) in `_lookup_restriction_uuid`.
Handles UUID vs label for dietary-restriction links.
"""
from __future__ import annotations

import datetime as _dt
import re
import uuid as _uuid
from typing import Iterable, Mapping, Any, List, Dict

from fastapi import HTTPException

from services.db_conn import Database

# ─────────── Table / column aliases ───────────
INGR_TABLE = "scan_ingredients"
INGR_COL_ING = "ingredient_name"  # column in schema
INGR_COL_STATUS = "verdict"

DIET_TABLE = "scan_dietary_restrictions"      # link table
DIET_REF_TABLE = "dietary_restrictions"       # lookup table with UUID PK + name
DIET_COL = "restriction_id"

UUID_RE = re.compile(r"^[0-9a-fA-F-]{32,36}$")

# ──────────────────────────────────────────────
async def _lookup_restriction_uuid(db: Database, code_or_uuid: str) -> str | None:
    """Return the UUID of a dietary restriction.

    * If `code_or_uuid` already looks like a UUID (32–36 hex chars ± dashes),
      return it directly.
    * Otherwise treat it as the **human‑readable label** (vegan / celiac /
      nut_allergy) and look up the corresponding UUID from
      `dietary_restrictions`.
    """
    if UUID_RE.fullmatch(code_or_uuid):
        return code_or_uuid  # already a UUID string

    row = await db.fetchrow(
        f"SELECT {DIET_COL} FROM {DIET_REF_TABLE} WHERE name = $1",
        code_or_uuid.lower(),
    )
    return row[DIET_COL] if row else None

# ──────────────────────────────────────────────
async def persist_scan(
    *,
    user_id: str,
    s3_image_url: str | None,
    final_verdict: str,
    restriction_ids: Iterable[str] | None,
    ingredients: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Insert a scan + its relations; returns the inserted scan row."""

    scan_id = str(_uuid.uuid4())
    now = _dt.datetime.utcnow()

    db = Database()
    await db.connect()
    try:
        # 1) main row
        row = await db.fetchrow(
            """
            INSERT INTO scans (scan_id, user_id, s3_image_url, final_verdict, scanned_at)
            VALUES ($1,      $2,      $3,            $4,           $5)
            RETURNING scan_id, user_id, s3_image_url, final_verdict, scanned_at
            """,
            scan_id,
            user_id,
            s3_image_url,
            final_verdict,
            now,
        )

        # 2) dietary restrictions link rows
        if restriction_ids:
            for rid in restriction_ids:
                uuid_val = await _lookup_restriction_uuid(db, str(rid))
                if uuid_val is None:
                    print(f"[WARN] Unknown dietary restriction label/UUID: {rid}")
                    continue  # skip unknowns instead of failing whole request
                await db.execute(
                    f"INSERT INTO {DIET_TABLE} (scan_id, {DIET_COL}) VALUES ($1, $2)",
                    scan_id,
                    uuid_val,
                )

        # 3) ingredient rows
        for item in ingredients:
            await db.execute(
                f"""
                INSERT INTO {INGR_TABLE} (scan_id, {INGR_COL_ING}, {INGR_COL_STATUS}, is_trace)
                VALUES ($1, $2, $3, $4)
                """,
                scan_id,
                str(item.get("ingredient") or item.get("name")),
                str(item.get("verdict") or item.get("status")),
                bool(item.get("is_trace", False)),
            )

        return dict(row)
    finally:
        await db.close()

# ──────────────────────────────────────────────
async def get_scan_history(user_id: str) -> List[Dict[str, Any]]:
    db = Database()
    await db.connect()
    try:
        rows = await db.fetch(
            """
            SELECT scan_id, s3_image_url, final_verdict, scanned_at
            FROM scans
            WHERE user_id = $1
            ORDER BY scanned_at DESC
            """,
            user_id,
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()

# ──────────────────────────────────────────────
async def get_scan_details(user_id: str, scan_id: str) -> Dict[str, Any]:
    db = Database()
    await db.connect()
    try:
        scan = await db.fetchrow(
            """
            SELECT scan_id, s3_image_url, final_verdict, scanned_at
            FROM scans
            WHERE scan_id = $1 AND user_id = $2
            """,
            scan_id,
            user_id,
        )
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        ing_rows = await db.fetch(
            f"""
            SELECT {INGR_COL_ING} AS ingredient,
                   {INGR_COL_STATUS} AS verdict,
                   is_trace
            FROM {INGR_TABLE}
            WHERE scan_id = $1
            ORDER BY {INGR_COL_ING}
            """,
            scan_id,
        )

        diet_rows = await db.fetch(
            f"SELECT {DIET_COL} FROM {DIET_TABLE} WHERE scan_id = $1",
            scan_id,
        )

        return {
            **dict(scan),
            "ingredients": [dict(r) for r in ing_rows],
            "restriction_ids": [r[DIET_COL] for r in diet_rows],
        }
    finally:
        await db.close()
