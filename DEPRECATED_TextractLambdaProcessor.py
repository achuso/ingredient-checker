import boto3
import base64
import uuid
import json

BUCKET_NAME = 'img-storage-s3-479'

class TextractLambdaProcessor:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.textract = boto3.client('textract')
        self.bucket = bucket_name

    def save_image_to_s3(self, image_b64):
        image_data = base64.b64decode(image_b64)
        image_id = str(uuid.uuid4())
        image_key = f"uploads/{image_id}.png"
        self.s3.put_object(Bucket=self.bucket, Key=image_key, Body=image_data)
        return image_key

    def extract_text(self, s3_key):
        response = self.textract.detect_document_text(
            Document={'S3Object': {'Bucket': self.bucket, 'Name': s3_key}}
        )
        return "\n".join(
            block["Text"] for block in response["Blocks"] if block["BlockType"] == "LINE"
        )

def lambda_handler(event, context):
    try:
        image_b64 = event.get('image_base64')
        if not image_b64:
            return {
                "statusCode": 400, 
                "body": json.dumps({"error": "No image provided."})
            }

        processor = TextractLambdaProcessor(BUCKET_NAME)
        s3_key = processor.save_image_to_s3(image_b64)
        extracted_text = processor.extract_text(s3_key)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "s3_key": s3_key,
                "text": extracted_text
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }