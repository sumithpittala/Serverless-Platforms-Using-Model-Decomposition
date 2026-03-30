import boto3
import botocore
import time

FUNCTION_NAME = 'MobileNetV3Lambda'
ZIP_PATH = 'lambda_deploy.zip'
LAYER_ARN = 'arn:aws:lambda:us-east-1:050451360541:layer:mobilenetv3-python-deps:1'

client = boto3.client('lambda')

def main():
    try:
        with open(ZIP_PATH, 'rb') as f:
            zip_bytes = f.read()
    except FileNotFoundError:
        print(f"Zip file not found: {ZIP_PATH}")
        return

    try:
        print(f'Updating function code for {FUNCTION_NAME} (publishing new version)...')
        resp = client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_bytes, Publish=True)
        print('Update function code response:')
        print(resp.get('ResponseMetadata', {}))
    except botocore.exceptions.ClientError as e:
        print('Failed to update function code:', e)
        return

    try:
        conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
    except botocore.exceptions.ClientError as e:
        print('Failed to get function configuration:', e)
        return

    existing_layers = conf.get('Layers') or []
    existing_arns = [l['Arn'] for l in existing_layers]
    if LAYER_ARN in existing_arns:
        print('Layer already attached; no change needed.')
    else:
        new_layers = existing_arns + [LAYER_ARN]
        print('Updating function configuration to attach layer:', LAYER_ARN)
        try:
            resp2 = client.update_function_configuration(FunctionName=FUNCTION_NAME, Layers=new_layers)
            print('Configuration update response (initiated):')
            print(resp2.get('ResponseMetadata', {}))
        except botocore.exceptions.ClientError as e:
            print('Failed to update function configuration:', e)
            return

        # wait for LastUpdateStatus to become Successful or Failed
        print('Waiting for configuration update to complete...')
        for i in range(30):
            time.sleep(1)
            conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
            status = conf.get('LastUpdateStatus')
            if status and status != 'InProgress':
                print('LastUpdateStatus =', status)
                break
        else:
            print('Timed out waiting for function configuration update.')

    print('Done. Function code updated and Layer attached (if needed).')
    print('You can now invoke the function or check its CloudWatch logs for runtime errors.')

if __name__ == '__main__':
    main()
