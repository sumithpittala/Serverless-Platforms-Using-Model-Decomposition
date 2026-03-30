import boto3
import botocore
import time

FUNCTION_NAME = 'MobileNetV3Lambda'
NEW_HANDLER = 'handler.lambda_handler'

client = boto3.client('lambda')

print('Current handler will be updated to', NEW_HANDLER)
for attempt in range(6):
    try:
        resp = client.update_function_configuration(FunctionName=FUNCTION_NAME, Handler=NEW_HANDLER)
        print('Update accepted:', resp.get('ResponseMetadata', {}))
        break
    except botocore.exceptions.ClientError as e:
        code = e.response.get('Error', {}).get('Code')
        print('Attempt failed:', code)
        if code in ('ResourceConflictException', 'TooManyRequestsException'):
            backoff = 2 ** attempt
            print('Retrying after', backoff, 's')
            time.sleep(backoff)
            continue
        else:
            print('Non-retriable error:', e)
            raise

print('Waiting for LastUpdateStatus to finish...')
for i in range(60):
    conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    status = conf.get('LastUpdateStatus')
    print('  status', i, status)
    if status != 'InProgress':
        print('Final status:', status)
        break
    time.sleep(1)
else:
    print('Timed out waiting for config update')

print('Done')
