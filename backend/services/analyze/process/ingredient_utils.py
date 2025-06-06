from __future__ import annotations

import re
from typing import List, Tuple, Optional

# flag to run spaCy for tests etc
USE_SPACY = False

_ING_HEADERS = [
    "içindekiler", "icindekiler",
    "icerik", "icerikler",
    "malzemeler", "bilesenler", "bileşenler"
]

_END_TRIGGERS = [
    re.compile(r"^\s*(besin|nutr(ition|ients)|saklama|storage|firma|manufact)", re.I),
    re.compile(r"^\s*(net ?ağırlık|net ?agirlik|net ?weight)\b", re.I),
    re.compile(r"^\s*[0-9]{1,3}\s?k?cal\b", re.I),
]

_TRACE_TRIGGERS = [
    re.compile(r"\beser miktarda\b", re.I),
    re.compile(r"\biz miktarda\b", re.I),
    re.compile(r"\bmay contain\b", re.I),
    re.compile(r"\btraces of\b", re.I),
    re.compile(r"\balerjen bilgisi\b", re.I),
    re.compile(r"\balerjen uyar", re.I),
]


def _is_end_line(line: str) -> bool:
    return any(p.search(line) for p in _END_TRIGGERS)

def _is_trace_line(line: str) -> bool:
    return any(p.search(line) for p in _TRACE_TRIGGERS)

def _extract_sections_regex(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    if not raw_text:
        return None, None

    lines: List[str] = raw_text.splitlines()

    # find header line index (tolerate minor OCR noise via simple fuzzy)
    start_idx: Optional[int] = None
    for i, line in enumerate(lines):
        low = line.lower()
        for hdr in _ING_HEADERS:
            if hdr in low or low.startswith(hdr.replace("ı", "i")):
                start_idx = i
                break
        if start_idx is not None:
            break
    if start_idx is None:
        return None, None

    ingredients, traces = [], []
    mode = "ingredients"
    bracket_depth = 0

    for line in lines[start_idx:]:
        low = line.lower().strip()

        if _is_end_line(low):
            break

        if mode == "ingredients" and _is_trace_line(low):
            mode = "traces"
            traces.append(line.strip())
            continue

        if mode == "ingredients":
            ingredients.append(line.strip())
            bracket_depth += line.count("(") + line.count("[") + line.count("{")
            bracket_depth -= line.count(")") + line.count("]") + line.count("}")
            if bracket_depth == 0 and re.search(r"[.;]\s*$", line):
                continue  # trace might follow
        else:
            if not line.strip():
                break
            traces.append(line.strip())

    ing_block = " ".join(ingredients)
    trace_block = " ".join(traces)

    for hdr in _ING_HEADERS:
        ing_block = re.sub(fr"\b{hdr}\b[:：]?", "", ing_block, flags=re.I)

    ing_block = re.sub(r"\s+", " ", ing_block).strip() or None
    trace_block = re.sub(r"\s+", " ", trace_block).strip() or None
    return ing_block, trace_block

if USE_SPACY:
    try:
        import spacy
        from spacy.matcher import Matcher
        from spacy.tokens import Doc, Span

        _nlp = spacy.blank("xx")
        _nlp.add_pipe("sentencizer")
        _matcher = Matcher(_nlp.vocab)
        _matcher.add("ING_HEADER", [[{"LOWER": hdr}] for hdr in _ING_HEADERS])

        def _extract_sections_spacy(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
            if not raw_text:
                return None, None
            doc: Doc = _nlp(raw_text)
            header_span: Optional[Span] = None
            for sent in doc.sents:
                if _matcher(sent):
                    header_span = sent
                    break
            if header_span is None:
                return _extract_sections_regex(raw_text)  # fallback

            # Map span start to line index
            lines = raw_text.splitlines()
            start_idx = next((i for i, l in enumerate(lines) if header_span.text.strip() in l), 0)
            # Reuse regex post‑processing for end/traces
            return _extract_sections_regex("\n".join(lines[start_idx:]))

    except ModuleNotFoundError:
        USE_SPACY = False


def extract_sections(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    # Return (ingredients, traces) using regex (default) or spaCy
    if USE_SPACY:
        return _extract_sections_spacy(raw_text)  # type: ignore[name‑defined]
    return _extract_sections_regex(raw_text)


def extract_ingredient_section(raw_text: str) -> Optional[str]:
    """ helper that returns only the ingredient block"""
    ing, _ = extract_sections(raw_text)
    return ing

if __name__ == "__main__":
    sample = (
        "NET AĞIRLIK 45g\n"
        "Icindekiler: Şeker, kakao kitlesi (15%), kakao yağı,\n"
        "yağsız süt tozu, emülgatör (soya lesitini), doğal vanilya aroması.\n"
        "Eser miktarda fındık ve yer fıstığı içerebilir.\n"
        "Besin Değerleri / Nutrition Facts…\n"
    )
    print("USE_SPACY =", USE_SPACY)
    ing, trc = extract_sections(sample)
    print("ING:", ing)
    print("TRACE:", trc)
