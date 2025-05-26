# services/analyze/process/llm_service.py
from __future__ import annotations

import os, json, logging
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

_REGION      = os.getenv("AWS_REGION", "eu-central-1")
_MODEL_ID    = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240328-v1:0")
_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.2"))
_MAX_TOKENS  = int(os.getenv("BEDROCK_MAX_TOKENS", "1024"))
_ANTHROPIC_VERSION = "bedrock-2023-05-31"

bedrock_rt = boto3.client("bedrock-runtime", region_name=_REGION)


class LLMService:
    """Invoke Amazon Bedrock to classify ingredients & traces."""
    def __init__(self, model_id: str | None = None):
        self.model_id = model_id or _MODEL_ID

    # ------------------------------------------------------------------ public
    def classify_from_ocr_text(self, ocr_text: str, restrictions: List[str] | str) -> Dict[str, Any]:
        if isinstance(restrictions, str):
            restrictions = [restrictions]
        prompt = self._prompt_from_raw_text(ocr_text, restrictions)
        return self._invoke(prompt)

    def classify(
        self,
        ingredients: List[str],
        traces: List[str],
        restrictions: List[str],
    ) -> Dict[str, Any]:
        prompt = self._prompt_from_lists(ingredients, traces, restrictions)
        return self._invoke(prompt)

    # ------------------------------------------------------------------ core
    def _invoke(self, prompt: str) -> Dict[str, Any]:
        body = {
            "anthropic_version": _ANTHROPIC_VERSION,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": _MAX_TOKENS,
            "temperature": _TEMPERATURE,
        }
        try:
            res = bedrock_rt.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
        except ClientError as e:
            logger.error("Bedrock invocation error: %s", e.response["Error"])
            raise

        raw = res["body"].read()
        logger.debug("Bedrock raw response ≈ %s", raw[:400])
        outer = json.loads(raw)
        assistant_text = outer.get("content", [{}])[0].get("text", "")
        return json.loads(assistant_text)

    @staticmethod
    def _prompt_from_raw_text(text: str, restrictions: str | list[str]) -> str:
        # Always coerce to list
        if isinstance(restrictions, str):
            restrictions = [restrictions]

        diets = ", ".join(restrictions)

        return (
            "SYSTEM: You are an expert food-label analyst.\n"
            f"The consumer follows these dietary restrictions: {diets}.\n"
            "• vegan means absolutely NO animal-derived ingredients or traces "
            "(meat, milk, cheese, yoghurt, egg, honey, gelatin, carmine, etc.).\n"
            "• celiac / gluten-free  means absolutely NO gluten-containing cereals or traces "
            "(wheat, barley, rye, malt, spelt, bulgur, couscous, beer, etc.).\n"
            "• nut allergy  means absolutely NO tree-nuts or peanuts, and no traces "
            "(almond, hazelnut, walnut, pecan, pistachio, cashew, macadamia, Brazil-nut, "
            "peanut butter, nut oils, gianduja, praline, etc.).\n\n"

            "EXAMPLES (guide only – do not copy into the answer):\n"
            "  \"İnek sütü\"                     → definitely unsafe (dairy vs vegan)\n"
            "  \"Su\"                            → safe\n"
            "  \"Pastorize yumurta sansi\"       → interpret as "
            "\"Pastörize yumurta sarısı\"       → definitely unsafe (egg vs vegan)\n"
            "  \"cikolata\"                      → interpret as "
            "\"çikolata\"                       → maybe unsafe (depends on milk content)\n\n"

            "OCR_LABEL_TEXT_START\n" + text + "\nOCR_LABEL_TEXT_END\n\n"

            "TASKS:\n"
            "1. Locate the complete *Ingredients* list and any trace / "
            "\"eser miktarda / içerebilir / may contain\" sentences.\n"
            "2. Correct obvious Turkish OCR errors:\n"
            "   – restore missing diacritics (ç, ğ, ı/İ, ö, ş, ü)\n"
            "   – fix common swaps like “sansi”→“sarısı”, “yogurt”→“yoğurt”, etc., "
            "when context makes intent clear.\n"
            "3. Move items to the correct section if misplaced.\n"
            "4. For **every** item decide ONE label:\n"
            "     • safe – compatible with ALL listed diets\n"
            "     • maybe unsafe – source uncertain; could violate\n"
            "     • definitely unsafe – clearly violates AT LEAST one diet\n\n"

            "Return ONLY the following minified JSON (no extra keys or text):\n"
            "{\"ingredients\":{<name>:{\"status\":<label>},…},"
            "\"traces\":{<name>:{\"status\":<label>},…}}"
        )



    @staticmethod
    def _prompt_from_lists(
        ingredients: List[str],
        traces: List[str],
        restrictions: List[str],
    ) -> str:
        ing   = "\n".join(f"- {i}" for i in ingredients) or "(none)"
        trc   = "\n".join(f"- {t}" for t in traces) or "(none)"
        restr = ", ".join(restrictions)
        return (
            f"User diets: {restr}.\n"
            "LIST A (ingredients):\n" + ing + "\n"
            "LIST B (traces):\n"      + trc + "\n\n"
            "Move items if mis-categorised, label each, return minified JSON "
            "with the same schema as above."
        )
