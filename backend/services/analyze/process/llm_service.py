from __future__ import annotations

import os, json, logging, re
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# ─────────── env / constants ───────────
_REGION      = os.getenv("AWS_REGION", "eu-central-1")
_MODEL_ID    = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240328-v1:0")
_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0"))      # 0 to be more deterministic
_MAX_TOKENS  = int(os.getenv("BEDROCK_MAX_TOKENS", "1024"))
_ANTHROPIC_VERSION = "bedrock-2023-05-31"

bedrock_rt = boto3.client("bedrock-runtime", region_name=_REGION)

JSON_RE = re.compile(r'JSON\s*:\s*(\{.*\})', re.DOTALL)


class LLMService:
    def __init__(self, model_id: str | None = None):
        self.model_id = model_id or _MODEL_ID

    # ─── public helpers ────────────────────────────────────────────
    def classify_from_ocr_text(
        self,
        ocr_text: str,
        restrictions: List[str] | str,
    ) -> Dict[str, Any]:
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

    # Bedrock call & JSON extraction
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

        # Bedrock returns a JSON wrapper → extract assistant text
        assistant_text = json.loads(res["body"].read()) \
                             .get("content", [{}])[0] \
                             .get("text", "")

        # Find the JSON blob after the 'JSON:' prefix
        m = JSON_RE.search(assistant_text)
        if not m:
            logger.error("LLM response missing JSON:\n%s", assistant_text)
            raise ValueError("LLM did not return JSON payload")
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError as err:
            logger.error("Bad JSON from LLM: %s\nBlob:\n%s", err, m.group(1))
            raise

    # prompt builders
    @staticmethod
    def _prompt_from_raw_text(text: str, restrictions: list[str]) -> str:
        active = ", ".join(restrictions)

        return (
            "SYSTEM: You are an expert food-label analyst. Your job is to assess "
            "whether Turkish ingredients are suitable for consumers based on their "
            "dietary restrictions.\n\n"

            f"ACTIVE DIETS for this user: **{active}**. "
            "Ignore diets that are not active when deciding safety.\n\n"

            "AVAILABLE DIETS & TYPICAL FORBIDDEN KEYWORDS (not exhaustive):\n"
            "1. vegan         – cannot eat animal-derived products (süt, peynir, yoğurt, tereyağ, yumurta, et…)\n"
            "2. celiac        – cannot eat gluten sources (buğday, arpa, malt, çavdar, kuskus, bulgur…)\n"
            "3. nut_allergy   – cannot eat tree-nuts / peanuts (badem, fındık, fıstık, ceviz, pecan…)\n\n"

            "LABELS (choose ONE):\n"
            "  safe              – clearly allowed for **all active** diets.\n"
            "  definitely unsafe – contains a forbidden keyword for **any active** diet.\n"
            "  maybe unsafe      – origin genuinely ambiguous *after* OCR fixes.\n\n"

            "HARD RULE: If an ingredient or trace text **contains** a forbidden keyword "
            "for an active diet, label it \"definitely unsafe\" (never \"maybe\"/\"safe\").\n\n"

            "TRACES: Sentences like “eser miktarda … içerebilir / may contain …”. "
            "Evaluate trace items with the *same* labels—if the trace violates a "
            "diet, it is \"definitely unsafe\".\n\n"

            "OCR NORMALISATION\n"
            "- Restore missing Turkish diacritics (ç, ğ, ı/İ, ö, ş, ü).\n"
            "- Fix obvious Turkish OCR swaps (e.g. “sansi” → “sarısı”, “yogurt” → “yoğurt”).\n"
            "- Remove OCR artifacts like “\n” or “#” that are not part of the ingredient text.\n\n"

            "EXAMPLES:\n"
            "  \"inek sütü\"                 -> definitely unsafe for vegan (dairy)\n"
            "  \"arpa maltı\"                -> definitely unsafe for celiac (gluten)\n"
            "  \"fındık aroması\"            -> definitely unsafe for nut_allergy (nut)\n"
            "  \"karamel\"                   -> maybe unsafe for vegan (origin unclear)\n"
            "  \"baharat karışımı\"          -> safe for vegan (spices are plant-based)\n"
            "  Trace: \"Eser miktarda fıstık içerebilir\" -> definitely unsafe for nut_allergy (trace)\n\n"

            "# OCR_START\n" + text + "\n# OCR_END\n\n"

            "STEP 1 – Reason briefly (<120 words): list each ingredient or trace and "
            "why you chose the label.\n"
            "STEP 2 – On a NEW line starting with `JSON:`, output only the minified JSON:\n"
            "JSON:{\"ingredients\":{name:{\"status\":label},…},"
            "\"traces\":{name:{\"status\":label},…}}\n"
            "Where ingredients refer to the main ingredient list, and traces "
            "refer to the trace list.\n"
            "Example input string for vegan class:\n"
            "İÇİNDEKİLER: Su, Şeker, Kakao Yağı, Yağsız Süt Tozu, Emülgatör (Soya Lesitini), Doğal Aroma\n"
            "ESER MİKTARDA FISTIK, BADEM VE FINDIK İÇEREBİLİR.\n"
            "Example output JSON:\n"
            "{\"ingredients\":{\"Su\":{\"status\":\"safe\"},"
            "\"Şeker\":{\"status\":\"safe\"},"
            "\"Kakao Yağı\":{\"status\":\"safe\"},"
            "\"Yağsız Süt Tozu\":{\"status\":\"definitely unsafe\"},"
            "\"Emülgatör (Soya Lesitini)\":{\"status\":\"safe\"},"
            "\"Doğal Aroma\":{\"status\":\"maybe unsafe\"}},"
            "\"traces\":{\"FISTIK\":{\"status\":\"safe\"},"
            "\"BADEM\":{\"status\":\"safe\"},"
            "\"FINDIK\":{\"status\":\"safe\"}}}\n"
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
            "SYSTEM: You classify food ingredients for dietary compliance.\n"
            f"User diets: {restr}\n\n"
            "Same LABEL rules as above.\n\n"
            "INGREDIENT LIST:\n" + ing + "\n\n"
            "TRACE LIST:\n" + trc + "\n\n"
            "Return reasoning then a final line:\n"
            "JSON:{\"ingredients\":{...},\"traces\":{...}}"
        )
