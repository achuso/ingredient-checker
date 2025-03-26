import boto3
import base64
import json
import argparse
import os
import sys

DEFAULTS = {
    'profile_name': 'lambda-dev-user',
    'function_name': 'image_pipeline_fn'
}

class TextractLambdaClient:
    def __init__(self, profile_name: str, function_name: str):
        # Environment variables (they're in the project directory)
        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = './.aws/credentials'
        os.environ['AWS_CONFIG_FILE'] = './.aws/config'

        self.session = boto3.Session(profile_name=profile_name)
        self.lambda_client = self.session.client('lambda')
        self.function_name = function_name

    def encode_image(self, image_path: str) -> str:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"File '{image_path}' not found.")
        
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            return base64.b64encode(image_bytes).decode('utf-8')

    def invoke(self, image_path: str) -> dict:
        image_b64 = self.encode_image(image_path)
        payload = {"image_base64": image_b64}

        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        raw_payload = json.load(response['Payload'])

        body = raw_payload.get('body')
        if isinstance(body, str):
            try:
                parsed_body = json.loads(body)
                print("Parsed body:", parsed_body)
                print("Type:", type(parsed_body))
                return parsed_body
            except json.JSONDecodeError:
                print("Couldn't parse body as JSON")
                return {"error": body}
        else:
            return body

def main():
    parser = argparse.ArgumentParser(description='Invoke Lambda with image.')
    parser.add_argument('image_path', help='Path to the image file')
    parser.add_argument('--profile', default=DEFAULTS['profile_name'], help='AWS profile to use')
    parser.add_argument('--function', default=DEFAULTS['function_name'], help='Lambda fn. name')

    args = parser.parse_args()

    try:
        invoker = TextractLambdaClient(profile_name=args.profile, function_name=args.function)
        result = invoker.invoke(args.image_path)

        print("Extracted text:")
        print(result['text'])

        print("\nFull response:")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()