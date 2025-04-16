import re
import unicodedata
from difflib import get_close_matches

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

def extract_ingredients(text: str) -> list[str]:
    lines = text.splitlines()

    start_idx = -1
    ingredients_lines = []

    # Fuzzy match for "içindekiler" in any line
    for i, line in enumerate(lines):
        norm_line = normalize(line)
        words = re.sub(r"[^\w\s]", "", norm_line).split()
        match = get_close_matches("icindekiler", words, n=1, cutoff=0.7)
        if match:
            # Clean the line by removing up to and including the match
            keyword_idx = norm_line.find(match[0])
            if keyword_idx != -1:
                header_cleaned = line[keyword_idx + len(match[0]):].strip(": -").strip()
                if header_cleaned:
                    ingredients_lines.append(header_cleaned)
            start_idx = i
            break

    if start_idx == -1:
        return []

    # Cutoff terms aka signals for the end of ingredient section
    cutoff_keywords = [
        "eser miktarda", "iz miktarda", "enerji", "besin", "saklama", "tüketim",
        "net agirlik", "net ağırlık", "kullanim", "kullanım", "tett", "serin",
        "gida isletmecisi", "gıda işletmecisi", "uret", "üret", "firma", "adres"
    ]

    for line in lines[start_idx + 1:]:
        normalized = normalize(re.sub(r"[^\w\s]", "", line))
        if any(kw in normalized for kw in cutoff_keywords):
            break
        if re.match(r"^[0-9\s]+g$", line) or re.search(r"\d{2}\.\d{2}", line):
            break
        ingredients_lines.append(line)

    # Combine all lines into one string
    full = " ".join(ingredients_lines).replace(" ,", ",").strip()

    # Smart split (commas outside parens, long text split)
    ingredients = []
    part = ""
    depth = 0
    MAX_LEN = 180
    MAX_DEPTH = 3

    for char in full:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)

        if (char == "," and depth == 0) or (len(part) > MAX_LEN and depth == 0) or (depth > MAX_DEPTH):
            ingredients.append(part.strip())
            part = ""
        else:
            part += char

    if part.strip():
        ingredients.append(part.strip())

    return ingredients
