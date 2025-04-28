import re
import unicodedata
from difflib import get_close_matches

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

def contains_fuzzy(text: str, keywords: list[str], cutoff=0.8) -> bool:
    words = text.split()
    for word in words:
        if get_close_matches(word, keywords, n=1, cutoff=cutoff):
            return True
    return False

def extract_ingredients_and_traces(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()

    start_idx = -1
    ingredients_lines = []
    trace_lines = []
    
    for i, line in enumerate(lines):
        norm_line = normalize(line)
        words = re.sub(r"[^\w\s]", "", norm_line).split()
        match = get_close_matches("icindekiler", words, n=1, cutoff=0.7)
        if match:
            keyword_idx = norm_line.find(match[0])
            if keyword_idx != -1:
                header_cleaned = line[keyword_idx + len(match[0]):].strip(": -").strip()
                if header_cleaned:
                    ingredients_lines.append(header_cleaned)
            start_idx = i
            break

    if start_idx == -1:
        return [], []

    cutoff_keywords = [
        "eser miktarda", "iz miktarda", "may contain", "traces of", "enerji", "besin", "saklama", 
        "tuketim", "net agirlik", "net ağırlık", "kullanim", "kullanım", "tett", "serin",
        "gida isletmecisi", "gıda işletmecisi", "uret", "üret", "firma", "adres"
    ]

    inline_cutoffs = [
        "gida kodeksi", "fermente", "uretilmistir", "üretim", "tebligi", "parti numarasi",
        "tüketim tarihi", "saklayiniz", "serin yerde", "ambalaj", "miktarda"
    ]

    def should_cut(normalized_line: str, raw_line: str) -> bool:
        checks = [
            lambda: any(kw in normalized_line for kw in cutoff_keywords),
            lambda: any(phrase in normalized_line for phrase in inline_cutoffs),
            lambda: contains_fuzzy(normalized_line, inline_cutoffs),
            lambda: re.match(r"^[0-9\s]+g$", raw_line) is not None,
            lambda: re.search(r"\d{2}\.\d{2}", raw_line) is not None
        ]
        return any(check() for check in checks)

    collecting_traces = False

    for line in lines[start_idx + 1:]:
        normalized = normalize(re.sub(r"[^\w\s]", "", line))

        if should_cut(normalized, line):
            break

        if not collecting_traces:
            if "eser miktarda" in normalized or "iz miktarda" in normalized or "may contain" in normalized or "traces of" in normalized:
                collecting_traces = True
                trace_lines.append(line)
            else:
                ingredients_lines.append(line)
        else:
            trace_lines.append(line)

    def split_lines_into_ingredients(lines: list[str]) -> list[str]:
        full = " ".join(lines).replace(" ,", ",").strip()

        ingredients = []
        part = ""
        round_depth = 0
        square_depth = 0
        MAX_LEN = 250
        MAX_DEPTH = 2

        def finalize_part(p):
            p = p.strip()
            norm = normalize(p)
            for phrase in inline_cutoffs:
                if phrase in norm or contains_fuzzy(norm, inline_cutoffs):
                    period_index = p.find(".")
                    phrase_index = norm.find(phrase)
                    if 0 <= period_index < phrase_index:
                        return p[:period_index].strip()
                    else:
                        return p[:phrase_index].strip()
            return p

        for i, char in enumerate(full):
            if char in "([)]":
                if char == "(":
                    round_depth += 1
                elif char == ")":
                    round_depth = max(0, round_depth - 1)
                elif char == "[":
                    square_depth += 1
                elif char == "]":
                    square_depth = max(0, square_depth - 1)

            next_char = full[i+1] if i + 1 < len(full) else ""
            force_boundary = (
                part.endswith(")") or part.endswith("]") or
                part.strip().startswith(")") or part.strip().startswith("]") or
                (char == "." and next_char == " ")
            )

            should_split = (
                (char == "," and round_depth == 0 and square_depth == 0) or
                (len(part) > MAX_LEN and round_depth == 0 and square_depth == 0) or
                (round_depth > MAX_DEPTH or square_depth > MAX_DEPTH) or
                force_boundary
            )

            if should_split:
                cleaned = finalize_part(part)
                if cleaned:
                    ingredients.append(cleaned)
                part = ""
            else:
                part += char

        if part.strip():
            cleaned = finalize_part(part)
            if cleaned:
                ingredients.append(cleaned)

        return ingredients

    ingredients = split_lines_into_ingredients(ingredients_lines)
    traces = split_lines_into_ingredients(trace_lines)

    return ingredients, traces
