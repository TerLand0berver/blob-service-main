from fastapi import UploadFile
import boto3
import requests
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from botocore.client import Config

from store.utils import store_filename
from config import (
    S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, S3_REGION, S3_API, S3_DOMAIN, S3_SPACE, S3_SIGN_VERSION,
    FILE_API_ENDPOINT, FILE_API_KEY,
)


def create_s3_client():
    config = Config(signature_version=S3_SIGN_VERSION) if S3_SIGN_VERSION else None
    if S3_DOMAIN and len(S3_DOMAIN) > 0:
        # Cloudflare R2 Storage
        return boto3.client(
            "s3",
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            endpoint_url=S3_API,
            config=config,
        )

    return boto3.client(
        "s3",
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=config,
    )


async def process_s3(file: UploadFile) -> str:
    """Process image and return its s3 url."""

    filename = store_filename(file.filename)

    try:
        client = create_s3_client()
        client.upload_fileobj(
            file.file,
            S3_BUCKET,
            filename,
            ExtraArgs={"ACL": "public-read"},
        )

        return f"{S3_SPACE}/{filename}"
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise ValueError(f"AWS credentials not found: {e}")
    except ClientError as e:
        raise ValueError(f"AWS S3 error: {e}")
    except Exception as e:
        raise ValueError(f"S3 error: {e}")


async def process_file_api(file: UploadFile) -> str:
    """
    Upload file to File API service and return markdown formatted link
    """
    try:
        filename = store_filename(file.filename)
        url = f"{FILE_API_ENDPOINT}/v1/file"
        headers = {}
        if FILE_API_KEY:
            headers['Authorization'] = FILE_API_KEY

        files = {'file': (filename, file.file, file.content_type)}
        response = requests.post(url, files=files, headers=headers)
        response.raise_for_status()
        
        # Get the URL from response
        result = response.json()
        file_url = result.get('url', '').strip()
        
        # Return markdown formatted link with spaces before and after
        return f" [{filename}]({file_url}) "
        
    except Exception as e:
        raise ValueError(f"File API upload error: {str(e)}")
