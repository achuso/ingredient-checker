from PIL import Image, ImageEnhance, ImageFilter, ImageStat, ImageOps
import io
import boto3
import base64
import uuid
import os
import functools
import logging

from fastapi.concurrency import run_in_threadpool

BUCKET_NAME = "img-storage-s3-479"
logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client("s3")

@functools.lru_cache(maxsize=1)
def get_textract_client():
    return boto3.client("textract")


class TextractProcessor:
    def __init__(self, bucket_name=BUCKET_NAME):
        self.s3 = get_s3_client()
        self.textract = get_textract_client()
        self.bucket = bucket_name

    def _preprocess_image(self, image_data: bytes) -> bytes:
        """Preprocess image with OCR-friendly enhancements."""
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        width, height = img.size

        # Resize if img too big
        if max(width, height) > 1500: img.thumbnail((1500, 1500))
        # Grayscale
        gray = img.convert("L")
        # Contrast adjustment based on brightness
        brightness = ImageStat.Stat(gray).mean[0]
        contrast_boost = 2.0 if brightness < 100 else 1.5
        contrast = ImageEnhance.Contrast(gray).enhance(contrast_boost)

        sharpened = contrast.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=5))

        # Light padding
        padded = ImageOps.expand(sharpened, border=10, fill='white')
        # Convert to RGB and save
        final = padded.convert("RGB")
        output = io.BytesIO()
        final.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()


    def save_image_to_s3(self, image_b64: str) -> str:
        image_data = base64.b64decode(image_b64)
        compressed_data = self._preprocess_image(image_data)
        image_id = str(uuid.uuid4())
        image_key = f"uploads/{image_id}.jpg"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=image_key,
            Body=compressed_data,
            ContentType='image/jpeg'
        )
        logger.info(f"Image uploaded to S3 at key: {image_key}")
        return image_key

    def extract_text(self, s3_key: str) -> str:
        response = self.textract.detect_document_text(
            Document={'S3Object': {'Bucket': self.bucket, 'Name': s3_key}}
        )
        lines = []
        for block in response["Blocks"]:
            if block["BlockType"] == "LINE":
                text = block["Text"]
                confidence = block.get("Confidence", 0)
                logger.debug(f"Line: '{text}' (Confidence: {confidence:.2f}%)")
                lines.append(text)
        return "\n".join(lines)
