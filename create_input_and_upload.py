<<<<<<< HEAD
"""Create an input tensor from an image and optionally upload to S3.

Usage examples:
  python create_input_and_upload.py --image dog.jpg --bucket mobilenetv3-bucket --key mobilenetv3/input.npy --upload
  python create_input_and_upload.py --image dog.jpg --out input.npy

This script keeps the original behavior but adds CLI and basic validation.
"""

import argparse
from pathlib import Path
import numpy as np
import boto3

try:
	import tensorflow as tf
except Exception:
	tf = None


def make_input_array(image_path: Path):
	if tf is None:
		raise RuntimeError("TensorFlow is required to run this script. Install tensorflow in the venv.")
	img = tf.keras.preprocessing.image.load_img(str(image_path), target_size=(224, 224))
	arr = tf.keras.preprocessing.image.img_to_array(img)
	arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
	arr = np.expand_dims(arr, axis=0)
	return arr


def upload_to_s3(local_path: Path, bucket: str, key: str):
	s3 = boto3.client('s3')
	s3.upload_file(str(local_path), bucket, key)


def main():
	p = argparse.ArgumentParser(description='Create input.npy and optionally upload to S3')
	p.add_argument('--image', '-i', type=str, required=True, help='Path to image file')
	p.add_argument('--out', '-o', type=str, default='input.npy', help='Local output npy filename')
	p.add_argument('--bucket', '-b', type=str, default='mobilenetv3-bucket', help='S3 bucket name')
	p.add_argument('--key', '-k', type=str, default='mobilenetv3/input.npy', help='S3 key to upload to')
	p.add_argument('--upload', action='store_true', help='Upload the created file to S3')
	args = p.parse_args()

	img_path = Path(args.image)
	if not img_path.exists():
		raise SystemExit(f"Image not found: {img_path}")

	arr = make_input_array(img_path)
	out_path = Path(args.out)
	np.save(str(out_path), arr)
	print(f"Saved input array to {out_path}")

	if args.upload:
		upload_to_s3(out_path, args.bucket, args.key)
		print(f"Uploaded {out_path} to s3://{args.bucket}/{args.key}")


if __name__ == '__main__':
	main()
=======
"""Create an input tensor from an image and optionally upload to S3.

Usage examples:
  python create_input_and_upload.py --image dog.jpg --bucket mobilenetv3-bucket --key mobilenetv3/input.npy --upload
  python create_input_and_upload.py --image dog.jpg --out input.npy

This script keeps the original behavior but adds CLI and basic validation.
"""

import argparse
from pathlib import Path
import numpy as np
import boto3

try:
	import tensorflow as tf
except Exception:
	tf = None


def make_input_array(image_path: Path):
	if tf is None:
		raise RuntimeError("TensorFlow is required to run this script. Install tensorflow in the venv.")
	img = tf.keras.preprocessing.image.load_img(str(image_path), target_size=(224, 224))
	arr = tf.keras.preprocessing.image.img_to_array(img)
	arr = tf.keras.applications.mobilenet_v3.preprocess_input(arr)
	arr = np.expand_dims(arr, axis=0)
	return arr


def upload_to_s3(local_path: Path, bucket: str, key: str):
	s3 = boto3.client('s3')
	s3.upload_file(str(local_path), bucket, key)


def main():
	p = argparse.ArgumentParser(description='Create input.npy and optionally upload to S3')
	p.add_argument('--image', '-i', type=str, required=True, help='Path to image file')
	p.add_argument('--out', '-o', type=str, default='input.npy', help='Local output npy filename')
	p.add_argument('--bucket', '-b', type=str, default='mobilenetv3-bucket', help='S3 bucket name')
	p.add_argument('--key', '-k', type=str, default='mobilenetv3/input.npy', help='S3 key to upload to')
	p.add_argument('--upload', action='store_true', help='Upload the created file to S3')
	args = p.parse_args()

	img_path = Path(args.image)
	if not img_path.exists():
		raise SystemExit(f"Image not found: {img_path}")

	arr = make_input_array(img_path)
	out_path = Path(args.out)
	np.save(str(out_path), arr)
	print(f"Saved input array to {out_path}")

	if args.upload:
		upload_to_s3(out_path, args.bucket, args.key)
		print(f"Uploaded {out_path} to s3://{args.bucket}/{args.key}")


if __name__ == '__main__':
	main()
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
