from __future__ import annotations

import os
import json
import logging
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

    def classify_from_ocr_text(self, ocr_text: str, restrictions: List[str]) -> Dict[str, Any]:
        prompt = self._prompt_from_raw_text(ocr_text, restrictions)
        return self._invoke(prompt)

    def classify(self, ingredients: List[str], traces: List[str], restrictions: List[str]) -> Dict[str, Any]:
        prompt = self._prompt_from_lists(ingredients, traces, restrictions)
        return self._invoke(prompt)

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
        logger.debug("Bedrock raw response ≈ %s", raw[:300])
        outer = json.loads(raw)
        text  = outer.get("content", [{}])[0].get("text", "")
        return json.loads(text)
    
    @staticmethod
    def _prompt_from_raw_text(text: str, restrictions: List[str]) -> str:
        
        restr = ", ".join(restrictions)
        return (
            "SYSTEM: You are an expert food-label analyst.\n"
            "The consumer follows these dietary restrictions: " + restr + ".\n"
            "Work ONLY with Turkish ingredient terminology; ignore marketing "
            "copy, nutrition tables, dates, addresses, barcodes, etc.\n\n"

            "OCR_LABEL_TEXT_START\n" + text + "\nOCR_LABEL_TEXT_END\n\n"

            "TASKS:\n"
            "1. Find the full *Ingredients list* and any *May-contain / trace* "
            "sentences (keywords like \"eser miktarda\", \"iz miktarda\", "
            "\"may contain\", \"içerebilir\").\n"
            "2. Fix obvious OCR character errors (ç, ğ, ü, ş, ö, İ, etc.).\n"
            "3. Ensure that every item is in the correct section across ingredients and traces (move if misplaced).\n"
            "4. For EACH item assign **one** label:\n"
            "- safe              : fully compatible with every diet above\n"
            "- maybe unsafe      : could conflict depending on source/processing\n"
            "- definitely unsafe : clearly conflicts with at least 1 provided diet\n\n"

            "OUTPUT:\n"
            "Return ONLY this exact minified JSON—no comments, no extra keys:\n"
            "{\"ingredients\":{<name>:{\"status\":<label>},…},"
            "\"traces\":{<name>:{\"status\":<label>},…}}\n"
        )

    @staticmethod
    def _prompt_from_lists(ingredients: List[str], traces: List[str], restrictions: List[str]) -> str:
        ing   = "\n".join(f"- {i}" for i in ingredients) or "(none)"
        trc   = "\n".join(f"- {t}" for t in traces) or "(none)"
        restr = ", ".join(restrictions)
        return (
            "User diets: " + restr + ".\nLIST A (ingredients):\n" + ing + "\nLIST B (traces):\n" + trc + "\n"
            "Move items if mis‑categorised, label each, return minified JSON."
        )
