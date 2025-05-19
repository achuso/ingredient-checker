from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Tuple

__all__ = [
    "normalize",
    "contains_fuzzy",
    "fuzzy_clean_header",
    "isolate_ingredient_block",
    "find_trace_start",
    "smart_split",
    "trace_items",
    "extract_ingredients_and_traces",
]

# Constants

HEADER_VARIANTS = [
    "icindekiler",
    "içindekiler",
    "licindekiler",
    "lçindekiler",
    "icindekıler",
]

END_BLOCK_KEYWORDS = [
    "enerji",
    "besin degeri",
    "besin değer",
    "nutrition",
    "nutritional",
    "kalori",
]

TRACE_TRIGGERS = [
    "eser miktarda",
    "iz miktarda",
    "may contain",
    "traces of",
    "içerebilir",
]

# Regexes to remove boiler‑plate from trace sentences

TRACE_PREFIX_RE = re.compile(
    r"^(?:iz|eser)?\s*miktarda\s+|^may contain\s+|^traces of\s+", re.I
)
TRACE_SUFFIX_RE = re.compile(
    r"\b(icerebilir|içerebilir|olabilir|icerir|contains?)\b.*$", re.I
)

MIN_TOKEN_LEN = 4

RE_ACCENTS = re.compile(r"[^0-9a-zA-ZğüşöçıİĞÜŞÖÇ%.,()\[\] ]+")
RE_WHITESPACE_MULTI = re.compile(r"\s+")

# Core helpers

def normalize(text: str) -> str:
    """ASCII‑folded lower‑case string with collapsed whitespace."""
    if not text:
        return ""
    txt = text.lower().replace("ı", "i")
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(ch for ch in txt if unicodedata.category(ch) != "Mn")
    txt = RE_ACCENTS.sub("", txt)
    txt = RE_WHITESPACE_MULTI.sub(" ", txt).strip()
    return txt


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(a=a, b=b).ratio()


def contains_fuzzy(text: str, keywords: List[str], cutoff: float = 0.75) -> bool:
    norm = normalize(text)
    for kw in keywords:
        if kw in norm or _similar(norm, kw) >= cutoff:
            return True
        for tok in norm.split():
            if _similar(tok, kw.split()[0]) >= cutoff:
                return True
    return False

# Header isolation

def fuzzy_clean_header(text: str) -> str:
    if not text:
        return text
    raw = text.lstrip()
    prefix = normalize(raw[:35])
    for variant in HEADER_VARIANTS:
        if _similar(prefix[: len(variant)], variant) >= 0.8:
            idx = raw.find(":")
            if idx == -1:
                idx = raw.find("\n")
            if idx != -1:
                return raw[idx + 1 :].lstrip()
            return raw[len(variant) :].lstrip()
    return text


def isolate_ingredient_block(text: str) -> str:
    cleaned = fuzzy_clean_header(text)
    norm = normalize(cleaned)
    cut_pos = len(cleaned)
    for kw in END_BLOCK_KEYWORDS:
        idx = norm.find(kw)
        if idx != -1:
            cut_pos = min(cut_pos, idx)
    return cleaned[:cut_pos].strip()

# Trace helpers

def _nearest_sentence_boundary(text: str, idx: int) -> int:
    left_dot = text.rfind(".", 0, idx)
    left_nl = text.rfind("\n", 0, idx)
    boundary = max(left_dot, left_nl)
    return boundary + 1 if boundary != -1 else 0


def find_trace_start(text: str) -> int:
    norm = normalize(text)
    best_idx = len(text)
    for trigger in TRACE_TRIGGERS + ["miktarda", "contain"]:
        hit = norm.find(trigger)
        if hit != -1:
            best_idx = min(best_idx, hit)
    return _nearest_sentence_boundary(text, best_idx)

# Ingredient splitting

def _clean_token(token: str) -> str | None:
    tok = RE_WHITESPACE_MULTI.sub(" ", token.replace("\n", " ")).strip(" ,.;:\n\t")
    if not tok:
        return None
    if len(tok) < MIN_TOKEN_LEN and re.fullmatch(r"[^a-zA-ZğüşöçıİĞÜŞÖÇ]+", tok):
        return None
    return tok


def smart_split(text: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    depth_sq = depth_par = 0
    for ch in text:
        if ch == "[":
            depth_sq += 1
        elif ch == "]":
            depth_sq = max(0, depth_sq - 1)
        elif ch == "(":
            depth_par += 1
        elif ch == ")":
            depth_par = max(0, depth_par - 1)
        if ch in ",." and depth_sq == 0 and depth_par == 0:
            cleaned = _clean_token("".join(buf))
            if cleaned:
                parts.append(cleaned)
            buf.clear()
        else:
            buf.append(ch)
    cleaned = _clean_token("".join(buf))
    if cleaned:
        parts.append(cleaned)
    return parts

# Trace‑item extraction

def trace_items(sentence: str) -> List[str]:
    if not sentence:
        return []

    core = normalize(sentence)

    # Define bounds for all the 'traces'
    prefix_idx = None
    for kw in ("miktarda", "contain", "traces of"):
        pos = core.find(kw)
        if pos != -1:
            prefix_idx = pos + len(kw)
            break
    if prefix_idx is not None:
        core = core[prefix_idx:]

    for kw in ("icere", "içere", "olabilir", "contains"):
        pos = core.find(kw)
        if pos != -1:
            core = core[:pos]
            break

    core = core.strip()
    if not core:
        return []

    # Split commas/dots/'ve', bracket-aware
    pieces = smart_split(core)
    items: List[str] = []
    for p in pieces:
        for bit in re.split(r"(?:ve|and)", p):
            cleaned = _clean_token(bit)
            if cleaned and cleaned not in items:
                items.append(cleaned)
    return items

# Public pipeline

def _clean_trace_sentence(sentence: str) -> str | None:
    if not sentence:
        return None
    tok_list = sentence.strip().split()
    while tok_list and (len(tok_list[0]) < 4 or re.search(r"[^a-zA-ZğüşöçıİĞÜŞÖÇ]", tok_list[0])):
        tok_list.pop(0)
    if not tok_list:
        return None
    clean_sentence = " ".join(tok_list)
    clean_sentence = RE_WHITESPACE_MULTI.sub(" ", clean_sentence).capitalize()
    if not clean_sentence.endswith("."):
        clean_sentence += "."
    return clean_sentence


def extract_ingredients_and_traces(text: str) -> Tuple[List[str], List[str]]:
    if not text:
        return ([], [])

    block = isolate_ingredient_block(text)
    if not block:
        return ([], [])

    trace_start = find_trace_start(block)
    ingredient_part = block[:trace_start]
    trace_part = block[trace_start:]

    ingredients = smart_split(ingredient_part)

    trace_ingredients: List[str] = []
    for sentence in re.split(r"[.]", trace_part):
        sen = sentence.strip()
        if not sen:
            continue
        if contains_fuzzy(sen, TRACE_TRIGGERS, 0.6):
            for item in trace_items(sen):
                if item not in trace_ingredients:
                    trace_ingredients.append(item)
    return (ingredients, trace_ingredients)
    