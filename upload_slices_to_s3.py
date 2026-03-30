"""Upload ONNX slice files from the local `slices/` folder to S3.

Usage:
  python upload_slices_to_s3.py --bucket my-bucket --prefix mobilenetv3/slices/

This helper is useful for deploying the pre-sliced models to S3 so the
Lambda-based workflow can download them at runtime.
"""

import argparse
from pathlib import Path
import boto3


def upload_folder(folder: Path, bucket: str, prefix: str):
    s3 = boto3.client('s3')
    for p in sorted(folder.glob('slice_*.onnx')):
        key = prefix.rstrip('/') + '/' + p.name
        print(f'Uploading {p} -> s3://{bucket}/{key}')
        s3.upload_file(str(p), bucket, key)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--folder', type=str, default='slices', help='Local slices folder')
    p.add_argument('--bucket', type=str, required=True, help='S3 bucket name')
    p.add_argument('--prefix', type=str, default='mobilenetv3/slices/', help='S3 prefix to upload to')
    args = p.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        raise SystemExit(f'Folder not found: {folder}')

    upload_folder(folder, args.bucket, args.prefix)


if __name__ == '__main__':
    main()
"""
Upload ONNX model slices to S3 bucket.
"""
import boto3
import os
from pathlib import Path

BUCKET_NAME = "mobilenetv3-bucket"
SLICES_FOLDER = "slices"
S3_PREFIX = "mobilenetv3/slices"

def create_bucket_if_not_exists(bucket_name):
    """Create S3 bucket if it doesn't exist."""
    s3 = boto3.client('s3')
    
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket {bucket_name} already exists")
    except s3.exceptions.ClientError:
        # Bucket doesn't exist, create it
        try:
            s3.create_bucket(Bucket=bucket_name)
            print(f"✓ Created bucket: {bucket_name}")
        except Exception as e:
            print(f"✗ Error creating bucket: {e}")
            raise

def upload_slices(bucket_name, slices_folder, s3_prefix):
    """Upload all slice files to S3."""
    s3 = boto3.client('s3')
    
    if not os.path.exists(slices_folder):
        print(f"✗ Error: {slices_folder} directory not found")
        print("  Run 2_slice_model.py first to create slices")
        return
    
    slice_files = sorted([f for f in os.listdir(slices_folder) if f.endswith('.onnx')])
    
    if not slice_files:
        print(f"✗ No .onnx files found in {slices_folder}")
        return
    
    print(f"\nUploading {len(slice_files)} slices to s3://{bucket_name}/{s3_prefix}/...")
    
    for slice_file in slice_files:
        local_path = os.path.join(slices_folder, slice_file)
        s3_key = f"{s3_prefix}/{slice_file}"
        
        file_size = os.path.getsize(local_path) / (1024 * 1024)
        print(f"  Uploading {slice_file} ({file_size:.2f} MB)...", end=" ")
        
        try:
            s3.upload_file(local_path, bucket_name, s3_key)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
            return
    
    print(f"\n✓ All slices uploaded successfully!")

def main():
    """Main upload function."""
    print("=" * 60)
    print("UPLOAD SLICES TO S3")
    print("=" * 60)
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print("✗ Error: AWS credentials not configured")
        print(f"  {e}")
        return
    
    # Create bucket if needed
    create_bucket_if_not_exists(BUCKET_NAME)
    
    # Upload slices
    upload_slices(BUCKET_NAME, SLICES_FOLDER, S3_PREFIX)
    
    print("\n" + "=" * 60)
    print("UPLOAD COMPLETE")
    print("=" * 60)
    print(f"\nSlices available at: s3://{BUCKET_NAME}/{S3_PREFIX}/")

if __name__ == "__main__":
    main()



