import boto3
import functools
import logging
from services.analyze.process.ingredient_utils import extract_ingredients

logger = logging.getLogger(__name__)

BUCKET_NAME = "img-storage-s3-479"

@functools.lru_cache(maxsize=1)
def get_textract_client():
    return boto3.client("textract")

class OCRService:
    def __init__(self, bucket_name=BUCKET_NAME):
        self.bucket = bucket_name
        self.textract = get_textract_client()

    def extract_text(self, s3_key: str) -> str:
        try:
            response = self.textract.detect_document_text(
                Document={'S3Object': {'Bucket': self.bucket, 'Name': s3_key}}
            )
            lines = []
            for block in response.get("Blocks", []):
                if block["BlockType"] == "LINE":
                    lines.append(block["Text"])
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise

    def extract_ingredients_from_s3(self, s3_key: str) -> list[str]:
        text = self.extract_text(s3_key)
        ingredients = extract_ingredients(text)
        return ingredients
