import boto3
import base64
import uuid
import filetype
import os

BUCKET_NAME = os.getenv("BUCKET_NAME", "img-storage-s3-479")

class TextractProcessor:
    def __init__(self, bucket_name=BUCKET_NAME):
        self.s3 = boto3.client('s3')
        self.textract = boto3.client('textract')
        self.bucket = bucket_name

    def save_image_to_s3(self, image_b64: str) -> str:
        image_data = base64.b64decode(image_b64)
        image_id = str(uuid.uuid4())

        # ✅ Use filetype instead of imghdr (Python 3.13 compatible)
        kind = filetype.guess(image_data)
        file_ext = kind.extension if kind else "png"

        image_key = f"uploads/{image_id}.{file_ext}"

        self.s3.put_object(
            Bucket=self.bucket,
            Key=image_key,
            Body=image_data,
            ContentType=f'image/{file_ext}'
        )
        return image_key

    def extract_text(self, s3_key: str) -> str:
        response = self.textract.detect_document_text(
            Document={'S3Object': {'Bucket': self.bucket, 'Name': s3_key}}
        )
        return "\n".join(
            block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"
        )
    

    