import argparse
import logging
from pathlib import Path
import numpy as np
import boto3
from botocore.exceptions import ClientError

# Set up clean logging for the presentation console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
except ImportError:
    tf = None

def make_input_array(image_path: Path):
    """Processes an image into a MobileNetV3-ready NumPy tensor."""
    if tf is None:
        raise RuntimeError("TensorFlow not found. Please run: pip install tensorflow")
    
    logger.info(f"Processing image: {image_path.name}")
    img = tf.keras.preprocessing.image.load_img(str(image_path), target_size=(224, 224))
    arr = tf.keras.preprocessing.image.img_to_array(img)
    arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
    arr = np.expand_dims(arr, axis=0)
    return arr

def get_s3_client(use_localstack: bool):
    """Returns a boto3 client configured for LocalStack or AWS."""
    if use_localstack:
        return boto3.client(
            's3',
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1"
        )
    return boto3.client('s3')

def upload_to_s3(local_path: Path, bucket: str, key: str, use_localstack: bool):
    """Ensures bucket exists and uploads the file."""
    s3 = get_s3_client(use_localstack)
    
    # Check if bucket exists; if using localstack, create it if missing
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        if use_localstack:
            logger.info(f"Bucket '{bucket}' not found in LocalStack. Creating it...")
            s3.create_bucket(Bucket=bucket)
        else:
            logger.error(f"Bucket '{bucket}' does not exist on AWS.")
            return

    logger.info(f"Uploading {local_path.name} to s3://{bucket}/{key}...")
    s3.upload_file(str(local_path), bucket, key)
    logger.info("Upload Successful!")

def main():
    p = argparse.ArgumentParser(description='MobileNetV3 Input Generator & S3 Uploader')
    p.add_argument('--image', '-i', type=str, required=True, help='Path to input image')
    p.add_argument('--out', '-o', type=str, default='input.npy', help='Local .npy filename')
    p.add_argument('--bucket', '-b', type=str, default='mobilenetv3-bucket', help='S3 bucket name')
    p.add_argument('--key', '-k', type=str, default='mobilenetv3/input.npy', help='S3 object key')
    p.add_argument('--upload', action='store_true', help='Upload to S3/LocalStack')
    p.add_argument('--aws', action='store_true', help='Use real AWS instead of LocalStack')
    
    args = p.parse_args()
    img_path = Path(args.image)

    if not img_path.exists():
        logger.error(f"File not found: {args.image}")
        return

    try:
        # 1. Generate the tensor
        arr = make_input_array(img_path)
        
        # 2. Save locally
        out_path = Path(args.out)
        np.save(str(out_path), arr)
        logger.info(f"Saved tensor locally to: {out_path}")

        # 3. Handle S3 Upload
        if args.upload:
            # use_localstack is True unless --aws flag is provided
            use_localstack = not args.aws
            upload_to_s3(out_path, args.bucket, args.key, use_localstack)

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()