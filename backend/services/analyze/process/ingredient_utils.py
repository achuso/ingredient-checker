from __future__ import annotations
import re, unicodedata
from typing import List, Tuple

from flashtext import KeywordProcessor
from rapidfuzz import fuzz

# ───────────── normalisation helpers ─────────────
_RE_MULTI_WS = re.compile(r"\s+")
_RE_ACCENTS  = re.compile(r"[^\wğüşöçıİĞÜŞÖÇ%.,()\[\]'\" ]+")


def _norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'")  # curved → straight
    text = text.lower().replace("ı", "i")
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = _RE_ACCENTS.sub("", text)
    return _RE_MULTI_WS.sub(" ", text).strip()


# ───────────── phrase tables ─────────────
_HEADER_PHRASES = ["içindekiler", "icindekiler"]
_NUTRITION_KEYS = ["enerji", "besin degeri", "besin değer", "nutrition", "kalori"]

_TRACE_PHRASES = [
    "eser miktarda",
    "iz miktarda",
    "may contain",
    "traces of",
    "içerebilir",
]
_TRACE_NORM = [_norm(t) for t in _TRACE_PHRASES]

# OCR-garbled “miktarda” (leading char lost / quotes inserted)
_RE_GARBLED_MIKTARDA = re.compile(r"[^\w]?['’`´]?[\s\n]*[lz]?[\s\n]*miktarda", re.I)
# Truncated “içerebilir” tails
_RE_TAIL_ICEREBIL = re.compile(r"i?cerebil\w*", re.I)

# ───────────── ingredient parser ─────────────
class IngredientParser:
    _MIN_TOKEN_LEN = 4  # discard tokens shorter than this

    def __init__(self) -> None:
        self._kp_trace = KeywordProcessor(case_sensitive=False)
        self._kp_trace.add_keywords_from_list(_TRACE_PHRASES)

    # ---------- Public API ----------
    def parse(self, text: str) -> Tuple[List[str], List[str]]:
        if not text:
            return [], []
        ing_block, trace_block = self._extract_blocks(text)
        ingredients = self._split_ingredients(ing_block)
        traces      = self._extract_trace_items(trace_block)
        return ingredients, traces

    # ---------- Block splitter ----------
    def _extract_blocks(self, text: str) -> Tuple[str, str]:
        """
        Return (ingredient_section, trace_section).
        Robust to:
        • header on same line as product name
        • no header at all (returns "", "")
        • trigger phrases garbled by OCR
        """
        lines = text.splitlines()
        hdr_idx = self._find_header_line(lines)
        if hdr_idx is None:
            return "", ""

        hdr_line = lines[hdr_idx]
        norm_hdr = _norm(hdr_line)
        # safe max(): hits may be empty
        hits = [norm_hdr.find(h) for h in _HEADER_PHRASES if h in norm_hdr]
        pos  = max(hits) if hits else 0

        after_hdr = hdr_line[pos + len("içindekiler") :]
        if ":" in after_hdr:
            after_hdr = after_hdr.split(":", 1)[1]

        candidate_lines = [after_hdr] + lines[hdr_idx + 1 :]
        candidate = "\n".join(candidate_lines)

        # cut at nutrition table
        n_cand = _norm(candidate)
        cut = min(
            (n_cand.find(k) for k in _NUTRITION_KEYS if n_cand.find(k) != -1),
            default=len(candidate),
        )
        candidate = candidate[:cut]

        # --- locate trace start ---
        # 1) exact FlashText
        hit = self._kp_trace.extract_keywords(candidate, span_info=True)
        if hit:
            start = min(s for _, s, _ in hit)
            end_line = candidate.find("\n", start)
            if end_line == -1:
                end_line = len(candidate)
            return candidate[:start].strip(), candidate[start:end_line].strip()

        # 2) fuzzy garbled "miktarda"
        m = _RE_GARBLED_MIKTARDA.search(candidate)
        if m:
            start = m.start()
            end_line = candidate.find("\n", start)
            if end_line == -1:
                end_line = len(candidate)
            return candidate[:start].strip(), candidate[start:end_line].strip()

        return candidate.strip(), ""

    def _find_header_line(self, lines: List[str]) -> int | None:
        for i, ln in enumerate(lines):
            if any(fuzz.partial_ratio(_norm(ln), h) >= 85 for h in _HEADER_PHRASES):
                return i
        return None

    # ---------- Ingredient tokenizer ----------
    def _split_ingredients(self, block: str) -> List[str]:
        if not block:
            return []

        out, buf = [], []
        depth_sq = depth_par = 0

        def flush():
            token = "".join(buf).strip(" ,.;:\n\t")
            buf.clear()
            if (
                len(token) >= self._MIN_TOKEN_LEN
                and re.search(r"[a-zA-ZğüşöçıİĞÜŞÖÇ]", token)
            ):
                out.append(_RE_MULTI_WS.sub(" ", token))

        for ch in block:
            if ch == "[": depth_sq += 1
            elif ch == "]": depth_sq = max(0, depth_sq - 1)
            elif ch == "(": depth_par += 1
            elif ch == ")": depth_par = max(0, depth_par - 1)

            if ch in ",." and depth_sq == depth_par == 0:
                flush()
            else:
                buf.append(ch)
        flush()
        return out

    # ---------- Trace tokenizer ----------
    def _extract_trace_items(self, trace_block: str) -> List[str]:
        if not trace_block:
            return []
        # keep only up to first sentence delimiter
        sentence = re.split(r"[.;]", trace_block, maxsplit=1)[0]
        clean = _norm(sentence)
        for trg in _TRACE_NORM:
            clean = clean.replace(trg, "")
        clean = _RE_GARBLED_MIKTARDA.sub("", clean)
        clean = _RE_TAIL_ICEREBIL.sub("", clean)

        items: List[str] = []
        for p in self._split_ingredients(clean):
            n = _norm(p)
            if n and n not in (_norm(i) for i in items):
                items.append(p.strip())
        return items


# ---------- Legacy helper ----------
def extract_ingredients_and_traces(text: str):
    """Backwards-compat wrapper."""
    return IngredientParser().parse(text)
