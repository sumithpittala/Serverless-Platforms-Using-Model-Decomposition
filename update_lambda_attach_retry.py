import boto3
import botocore
import time

FUNCTION_NAME = 'MobileNetV3Lambda'
LAYER_ARN = 'arn:aws:lambda:us-east-1:050451360541:layer:mobilenetv3-python-deps:1'

client = boto3.client('lambda')

def main():
    print('Polling function LastUpdateStatus until not InProgress...')
    for i in range(60):
        conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        status = conf.get('LastUpdateStatus')
        print(f'  poll {i}: LastUpdateStatus={status}')
        if status != 'InProgress':
            break
        time.sleep(1)
    else:
        print('Timed out waiting for prior update to finish; will attempt attach anyway.')

    conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    existing_layers = conf.get('Layers') or []
    existing_arns = [l['Arn'] for l in existing_layers]

    if LAYER_ARN in existing_arns:
        print('Layer already attached; nothing to do.')
        return

    new_layers = existing_arns + [LAYER_ARN]

    print('Attempting to update function configuration to attach layer...')
    for attempt in range(6):
        try:
            resp = client.update_function_configuration(FunctionName=FUNCTION_NAME, Layers=new_layers)
            print('Update accepted (response metadata):', resp.get('ResponseMetadata', {}))
            break
        except botocore.exceptions.ClientError as e:
            code = e.response.get('Error', {}).get('Code')
            print(f'Attempt {attempt} failed with {code}:', e)
            if code in ('ResourceConflictException', 'TooManyRequestsException'):
                backoff = 2 ** attempt
                print(f'  Retrying after {backoff}s...')
                time.sleep(backoff)
                continue
            else:
                print('Non-retriable error, aborting.')
                return
    else:
        print('Failed to update configuration after retries.')
        return

    print('Waiting for configuration update to complete...')
    for i in range(60):
        conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        status = conf.get('LastUpdateStatus')
        print(f'  check {i}: LastUpdateStatus={status}')
        if status and status != 'InProgress':
            print('Configuration update status:', status)
            break
        time.sleep(1)
    else:
        print('Timed out waiting for configuration to finish.')

    print('Done attaching layer.')

if __name__ == '__main__':
    main()
