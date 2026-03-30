<<<<<<< HEAD
"""
Create a manifest JSON for ONNX slices and upload it to S3.

Usage:
  python create_s3_manifest.py --bucket mobilenetv3-bucket --prefix mobilenetv3/slices/

This writes `manifest.json` locally and uploads to `s3://{bucket}/{prefix.rstrip('/')}/manifest.json`.
"""
import argparse
import json
import os
from pathlib import Path
import boto3
from datetime import datetime


def build_manifest(folder: Path, bucket: str, prefix: str):
    files = sorted([p.name for p in folder.glob('slice_*.onnx')])
    if not files:
        raise SystemExit('No slice_*.onnx files found in ' + str(folder))
    prefix_clean = prefix.rstrip('/')
    keys = [f'{prefix_clean}/{fname}' for fname in files]
    manifest = {
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'bucket': bucket,
        'prefix': prefix_clean,
        'slices': keys,
        'count': len(keys),
    }
    return manifest


def upload_manifest(manifest: dict, bucket: str, prefix: str):
    s3 = boto3.client('s3')
    manifest_body = json.dumps(manifest, indent=2)
    key = prefix.rstrip('/') + '/manifest.json'
    s3.put_object(Bucket=bucket, Key=key, Body=manifest_body.encode('utf-8'), ContentType='application/json')
    return key


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--folder', type=str, default='slices', help='Local slices folder')
    p.add_argument('--bucket', type=str, required=True, help='S3 bucket name')
    p.add_argument('--prefix', type=str, default='mobilenetv3/slices/', help='S3 prefix where slices live')
    args = p.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        raise SystemExit(f'Folder not found: {folder}')

    manifest = build_manifest(folder, args.bucket, args.prefix)
    local_path = Path('slices') / 'manifest.json'
    with open(local_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print('Wrote local manifest:', str(local_path))

    key = upload_manifest(manifest, args.bucket, args.prefix)
    print(f'Uploaded manifest to s3://{args.bucket}/{key}')
=======
"""
Create a manifest JSON for ONNX slices and upload it to S3.

Usage:
  python create_s3_manifest.py --bucket mobilenetv3-bucket --prefix mobilenetv3/slices/

This writes `manifest.json` locally and uploads to `s3://{bucket}/{prefix.rstrip('/')}/manifest.json`.
"""
import argparse
import json
import os
from pathlib import Path
import boto3
from datetime import datetime


def build_manifest(folder: Path, bucket: str, prefix: str):
    files = sorted([p.name for p in folder.glob('slice_*.onnx')])
    if not files:
        raise SystemExit('No slice_*.onnx files found in ' + str(folder))
    prefix_clean = prefix.rstrip('/')
    keys = [f'{prefix_clean}/{fname}' for fname in files]
    manifest = {
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'bucket': bucket,
        'prefix': prefix_clean,
        'slices': keys,
        'count': len(keys),
    }
    return manifest


def upload_manifest(manifest: dict, bucket: str, prefix: str):
    s3 = boto3.client('s3')
    manifest_body = json.dumps(manifest, indent=2)
    key = prefix.rstrip('/') + '/manifest.json'
    s3.put_object(Bucket=bucket, Key=key, Body=manifest_body.encode('utf-8'), ContentType='application/json')
    return key


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--folder', type=str, default='slices', help='Local slices folder')
    p.add_argument('--bucket', type=str, required=True, help='S3 bucket name')
    p.add_argument('--prefix', type=str, default='mobilenetv3/slices/', help='S3 prefix where slices live')
    args = p.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        raise SystemExit(f'Folder not found: {folder}')

    manifest = build_manifest(folder, args.bucket, args.prefix)
    local_path = Path('slices') / 'manifest.json'
    with open(local_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print('Wrote local manifest:', str(local_path))

    key = upload_manifest(manifest, args.bucket, args.prefix)
    print(f'Uploaded manifest to s3://{args.bucket}/{key}')
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
