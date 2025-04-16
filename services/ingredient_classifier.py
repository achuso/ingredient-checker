import re
import unicodedata
from difflib import get_close_matches
from typing import List, Dict

class IngredientClassifier:
    def __init__(self):
        # Temporary rules, to be changed later
        self.rules = {
            "celiac": {
                "unsafe": ["buğday", "arpa", "malt", "çavdar", "irmik", "bulgur", "gluten", "buğday unu"],
                "maybe": ["yulaf", "nişasta", "modifiye nişasta", "aroma"],
                "safe": []
            },
            "vegan": {
                "unsafe": ["süt", "yumurta", "peynir", "jelatin", "kazein", "bal", "tereyağı", "yoğurt", "süt tozu"],
                "maybe": ["laktik asit", "vitamin d3"],
                "safe": []
            },
            "nut_allergy": {
                "unsafe": ["badem", "kaju", "fındık", "ceviz", "antep fıstığı", "yer fıstığı"],
                "maybe": [],
                "safe": []
            }
        }

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8").lower()

    def extract_ingredient_section(self, text: str) -> str:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "ingredient" in line.lower() or "içindekiler" in line.lower():
                return " ".join(lines[i:])
        return text  # Fallback to full text, if extraction fails

    def split_ingredients(self, text: str) -> List[str]:
        text = text.replace("\n", ",").replace(";", ",")
        parts = re.split(r",|\.", text)
        return [self.normalize(p.strip()) for p in parts if len(p.strip()) > 1]

    def classify(self, input_data: str | List[str], restriction: str) -> List[Dict[str, str]]:
        if isinstance(input_data, list):
            ingredients = [self.normalize(i) for i in input_data]
        else:
            extracted = self.extract_ingredient_section(input_data)
            ingredients = self.split_ingredients(extracted)

        rule = self.rules.get(restriction, {})
        all_known = rule.get("unsafe", []) + rule.get("maybe", []) + rule.get("safe", [])
        all_known_normalized = [self.normalize(i) for i in all_known]

        classified = []

        for item in ingredients:
            label = "unknown"
            if item in [self.normalize(i) for i in rule.get("unsafe", [])]:
                label = "unsafe"
            elif item in [self.normalize(i) for i in rule.get("maybe", [])]:
                label = "maybe"
            elif item in [self.normalize(i) for i in rule.get("safe", [])]:
                label = "safe"
            else:
                # Fuzzy matching
                match = get_close_matches(item, all_known_normalized, n=1, cutoff=0.8)
                if match:
                    idx = all_known_normalized.index(match[0])
                    matched_original = all_known[idx]
                    if matched_original in rule["unsafe"]:
                        label = "unsafe"
                    elif matched_original in rule["maybe"]:
                        label = "maybe"
                    elif matched_original in rule["safe"]:
                        label = "safe"

            classified.append({"ingredient": item, "status": label})

        return classified