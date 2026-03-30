<<<<<<< HEAD
import boto3
import json
import time

FUNCTION_NAME = 'MobileNetV3Lambda'
BUCKET = 'mobilenetv3-bucket'
INPUT_KEY = 'mobilenetv3/input.npy'
OUTPUT_KEY = 'mobilenetv3/intermediate_0.npy'
SLICE_ID = 0
TOTAL_SLICES = 5

client = boto3.client('lambda')
s3 = boto3.client('s3')

event = {
    'bucket': BUCKET,
    'slice_id': SLICE_ID,
    'total_slices': TOTAL_SLICES,
    'input_key': INPUT_KEY,
    'output_key': OUTPUT_KEY
}

print('Invoking function with event:')
print(json.dumps(event, indent=2))

resp = client.invoke(FunctionName=FUNCTION_NAME, InvocationType='RequestResponse', Payload=json.dumps(event).encode())

status_code = resp.get('StatusCode')
print('Invoke StatusCode:', status_code)

payload_stream = resp.get('Payload')
if payload_stream is not None:
    try:
        payload_text = payload_stream.read().decode()
        print('Payload:', payload_text)
    except Exception as e:
        print('Failed to read payload:', e)

# verify S3 object exists
print('Verifying S3 object:', BUCKET, OUTPUT_KEY)
try:
    head = s3.head_object(Bucket=BUCKET, Key=OUTPUT_KEY)
    print('S3 object exists, size:', head.get('ContentLength'))
except Exception as e:
    print('S3 head_object failed:', e)

print('Done')
=======
import boto3
import json
import time

FUNCTION_NAME = 'MobileNetV3Lambda'
BUCKET = 'mobilenetv3-bucket'
INPUT_KEY = 'mobilenetv3/input.npy'
OUTPUT_KEY = 'mobilenetv3/intermediate_0.npy'
SLICE_ID = 0
TOTAL_SLICES = 5

client = boto3.client('lambda')
s3 = boto3.client('s3')

event = {
    'bucket': BUCKET,
    'slice_id': SLICE_ID,
    'total_slices': TOTAL_SLICES,
    'input_key': INPUT_KEY,
    'output_key': OUTPUT_KEY
}

print('Invoking function with event:')
print(json.dumps(event, indent=2))

resp = client.invoke(FunctionName=FUNCTION_NAME, InvocationType='RequestResponse', Payload=json.dumps(event).encode())

status_code = resp.get('StatusCode')
print('Invoke StatusCode:', status_code)

payload_stream = resp.get('Payload')
if payload_stream is not None:
    try:
        payload_text = payload_stream.read().decode()
        print('Payload:', payload_text)
    except Exception as e:
        print('Failed to read payload:', e)

# verify S3 object exists
print('Verifying S3 object:', BUCKET, OUTPUT_KEY)
try:
    head = s3.head_object(Bucket=BUCKET, Key=OUTPUT_KEY)
    print('S3 object exists, size:', head.get('ContentLength'))
except Exception as e:
    print('S3 head_object failed:', e)

print('Done')
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
