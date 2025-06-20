import boto3, functools, io, logging
from typing import List

from PIL import Image  # Pillow – new lightweight dep
from services.analyze.process.ingredient_utils import IngredientParser

logger = logging.getLogger(__name__)
BUCKET_NAME = "img-storage-s3-479"

@functools.lru_cache(maxsize=1)
def _textract():
    return boto3.client("textract")

@functools.lru_cache(maxsize=1)
def _parser():
    return IngredientParser()

class OCRService:
    def __init__(self, bucket: str = BUCKET_NAME):
        self.bucket = bucket
        self.textract = _textract()
        self.s3 = boto3.client("s3")

    # helpers
    def _download_image_bytes(self, key: str) -> bytes:
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def _rotate_bytes(self, img_bytes: bytes, angle: int) -> bytes:
        if angle == 0:
            return img_bytes
        im = Image.open(io.BytesIO(img_bytes))
        rotated = im.rotate(angle, expand=True)
        buf = io.BytesIO()
        rotated.save(buf, format="JPEG")  # Textract handles JPEG/PNG
        return buf.getvalue()

    def _ocr_lines(self, img_bytes: bytes) -> List[str]:
        resp = self.textract.detect_document_text(Document={"Bytes": img_bytes})
        return [b["Text"] for b in resp.get("Blocks", []) if b["BlockType"] == "LINE"]

    # public API
    def extract_text(self, s3_key: str) -> str:
        try:
            original = self._download_image_bytes(s3_key)
        except Exception as e:
            logger.error(f"S3 download failed ({s3_key}): {e}")
            raise

        best_lines, best_len = [], 0
        for ang in (0, 90, 180, 270):
            try:
                img_b = self._rotate_bytes(original, ang)
                lines = self._ocr_lines(img_b)
            except Exception as e:
                logger.warning(f"OCR rotation {ang}° failed: {e}")
                continue

            total = sum(len(l) for l in lines)
            if total > best_len:
                best_len, best_lines = total, lines
            # quick exit: perfect upright usually yields > 100 chars
            if best_len > 100:
                break

        if not best_lines:
            raise RuntimeError("Textract returned no text on any rotation")

        return "\n".join(best_lines)

    def extract_ingredients_from_s3(self, s3_key: str) -> dict:
        text = self.extract_text(s3_key)
        ingredients, traces = _parser().parse(text)
        return {"ingredients": ingredients, "traces": traces}
