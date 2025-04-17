from PIL import Image, ImageEnhance
import io
import boto3
import base64
import uuid
import os
import functools
import logging
import cv2
import numpy as np
from services.ingredient_utils import extract_ingredients

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
        # Convert to numpy img
        np_img = np.frombuffer(image_data, np.uint8)
        cv_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Resize if needed
        max_dim = 1500
        h, w = cv_img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            cv_img = cv2.resize(cv_img, (int(w * scale), int(h * scale)))

        # Blur detection
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        BLUR_THRESHOLD = 100

        # Different preprocessing approaches based on blur score
        if blur_score >= BLUR_THRESHOLD:
            # Pillow-based light pipeline
            pil_img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)).convert("L")
            contrast = ImageEnhance.Contrast(pil_img).enhance(1.3)
            final = contrast.convert("RGB")
        else:
            # OpenCV heavy pipeline
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            padded = cv2.copyMakeBorder(thresh, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
            final = Image.fromarray(padded).convert("RGB")

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

    def extract_ingredient_lines(self, s3_key: str) -> list[str]:
        raw_text = self.extract_text(s3_key)
        return extract_ingredients(raw_text)
    