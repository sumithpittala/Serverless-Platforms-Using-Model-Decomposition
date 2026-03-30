import boto3
import zipfile
import io
import time
import json

FUNCTION_NAME = 'MobileNetV3Lambda'
BUCKET = 'mobilenetv3-bucket'
INPUT_KEY = 'mobilenetv3/input.npy'
OUTPUT_KEY = 'mobilenetv3/intermediate_0_smoke.npy'
ORIGINAL_ZIP = 'lambda_deploy.zip'
SMOKE_ZIP = 'lambda_smoke_deploy.zip'

# Minimal handler that copies the input object to output without importing numpy
HANDLER_PY = r'''
import boto3
import io

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = event['bucket']
    input_key = event['input_key']
    output_key = event['output_key']
    buf = io.BytesIO()
    s3.download_fileobj(bucket, input_key, buf)
    buf.seek(0)
    # echo back the same bytes
    s3.upload_fileobj(buf, bucket, output_key)
    return {'status': 'ok', 'echoed': output_key}
'''

client = boto3.client('lambda')
s3 = boto3.client('s3')

# create zip in-memory
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w') as z:
    z.writestr('handler.py', HANDLER_PY)
buf.seek(0)

print('Uploading smoke zip to function...')
resp = client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=buf.read(), Publish=True)
print('Updated function code, response status:', resp.get('ResponseMetadata', {}))

print('Waiting for code update to finish...')
for i in range(30):
    conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    status = conf.get('LastUpdateStatus')
    print(' status', i, status)
    if status != 'InProgress':
        break
    time.sleep(1)
print('Code update complete, status:', status)

# invoke
event = {
    'bucket': BUCKET,
    'slice_id': 0,
    'total_slices': 5,
    'input_key': INPUT_KEY,
    'output_key': OUTPUT_KEY
}
print('Invoking smoke handler...')
inv = client.invoke(FunctionName=FUNCTION_NAME, InvocationType='RequestResponse', Payload=json.dumps(event).encode())
print('Invoke status:', inv.get('StatusCode'))
try:
    payload = inv['Payload'].read().decode()
    print('Payload:', payload)
except Exception as e:
    print('Failed reading payload:', e)

# verify S3
print('Verifying S3 object exists...')
try:
    head = s3.head_object(Bucket=BUCKET, Key=OUTPUT_KEY)
    print('Found object, size:', head.get('ContentLength'))
except Exception as e:
    print('S3 check failed:', e)

# restore original zip
print('Restoring original function code from', ORIGINAL_ZIP)
try:
    with open(ORIGINAL_ZIP, 'rb') as f:
        client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=f.read(), Publish=True)
    print('Restore requested')
    # wait
    for i in range(30):
        conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        status = conf.get('LastUpdateStatus')
        print(' restore status', i, status)
        if status != 'InProgress':
            break
        time.sleep(1)
    print('Restore finished, status:', status)
except Exception as e:
    print('Failed to restore original code:', e)

print('Smoke test complete')
