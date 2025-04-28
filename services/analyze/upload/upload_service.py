import base64
import io
import uuid
from PIL import Image, ImageEnhance
import boto3
import functools
import logging

logger = logging.getLogger(__name__)

BUCKET_NAME = "img-storage-s3-479"

@functools.lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client("s3")

class UploadService:
    def __init__(self, bucket_name=BUCKET_NAME):
        self.bucket = bucket_name
        self.s3 = get_s3_client()

    def preprocess_image(self, image_data: bytes) -> bytes:
        input_stream = io.BytesIO(image_data)
        pil_img = Image.open(input_stream).convert("L")  # grayscale
        enhanced = ImageEnhance.Contrast(pil_img).enhance(1.4)  # boost contrast
        final = enhanced.convert("RGB")

        output = io.BytesIO()
        final.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()

    def upload_base64_image(self, image_base64: str) -> str:
        try:
            image_data = base64.b64decode(image_base64)
            processed_data = self.preprocess_image(image_data)
            image_id = str(uuid.uuid4())
            image_key = f"uploads/{image_id}.jpg"

            self.s3.put_object(
                Bucket=self.bucket,
                Key=image_key,
                Body=processed_data,
                ContentType="image/jpeg"
            )

            logger.info(f"Image uploaded to S3: {image_key}")
            return image_key
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise
