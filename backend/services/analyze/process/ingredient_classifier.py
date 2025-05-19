from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from typing import Iterable, List, Dict

_RULES_FILE = Path(__file__).with_name("rules.json")   # …or inject via __init__


def _normalize(text: str) -> str:
    # ASCII-fold Turkish chars, lower-case, collapse spaces
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s{2,}", " ", text).strip()


class IngredientClassifier:
    def __init__(self, rules_path: str | Path = _RULES_FILE):
        self.rules_path = Path(rules_path)
        self.rules: Dict[str, Dict[str, List[str]]] = self._load_rules()

        # pre-normalise rule terms for fast look-ups
        self.norm_rules: Dict[str, Dict[str, List[str]]] = {
            diet: {
                level: [_normalize(t) for t in terms]
                for level, terms in grouping.items()
            }
            for diet, grouping in self.rules.items()
        }

    def classify(
        self,
        ingredients: Iterable[str],
        restriction: str | Iterable[str],
    ) -> List[Dict[str, str]]:

        if isinstance(restriction, str): restrictions = [restriction]
        else: restrictions = list(restriction)

        restrictions = [r for r in restrictions if r in self.norm_rules]
        if not restrictions:
            raise ValueError("Unknown dietary restriction(s)")

        verdicts: List[Dict[str, str]] = []

        for raw in ingredients:
            norm = _normalize(raw)
            status = "safe"

            for r in restrictions:
                unsafe_terms = self.norm_rules[r]["unsafe"]
                maybe_terms = self.norm_rules[r]["maybe_unsafe"]

                if self._matches(norm, unsafe_terms):
                    status = "definitely unsafe"
                    break
                if status == "safe" and self._matches(norm, maybe_terms):
                    status = "maybe unsafe"
                    # keep checking; another diet might upgrade to unsafe

            verdicts.append({"ingredient": raw, "status": status})

        return verdicts

    def _load_rules(self) -> Dict[str, Dict[str, List[str]]]:
        with self.rules_path.open(encoding="utf-8") as fh:
            return json.load(fh)

    @staticmethod
    def _matches(text: str, terms: List[str]) -> bool:
        for term in terms:
            if term.startswith("e") and term[1:].isdigit():
                if term in text:
                    return True
            else:
                if re.search(rf"\b{re.escape(term)}\b", text):
                    return True
        return False
