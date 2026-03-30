<<<<<<< HEAD
import boto3
import sys
import json
from pathlib import Path

LAYER_ZIP = 'python.zip'
FUNCTION_ZIP = 'lambda_deploy.zip'
FUNCTION_NAME = 'ml-inference-slice-handler'
LAYER_NAME = 'mobilenetv3-python-deps'
RUNTIME = 'python3.10'

def publish_layer():
    if not Path(LAYER_ZIP).exists():
        print('Layer zip not found:', LAYER_ZIP)
        return None
    client = boto3.client('lambda')
    with open(LAYER_ZIP, 'rb') as f:
        resp = client.publish_layer_version(
            LayerName=LAYER_NAME,
            Content={'ZipFile': f.read()},
            CompatibleRuntimes=[RUNTIME],
            Description='Python dependencies for mobilenetv3 slices'
        )
    print('Published layer version:', resp.get('Version'))
    return resp


def update_function_code(layer_arn=None):
    if not Path(FUNCTION_ZIP).exists():
        print('Function zip not found:', FUNCTION_ZIP)
        return None
    client = boto3.client('lambda')
    with open(FUNCTION_ZIP, 'rb') as f:
        resp = client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=f.read(),
            Publish=True
        )
    print('Updated function code, status:', resp.get('LastUpdateStatus'))

    if layer_arn:
        # Get existing layers
        cfg = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        existing_layers = [l['Arn'] for l in cfg.get('Layers', [])]
        # prepend new layer
        new_layers = [layer_arn] + [a for a in existing_layers if a != layer_arn]
        client.update_function_configuration(FunctionName=FUNCTION_NAME, Layers=new_layers)
        print('Updated function configuration with new layer')
    return resp


if __name__ == '__main__':
    print('Publishing layer...')
    try:
        layer_resp = publish_layer()
    except Exception as e:
        print('Failed to publish layer:', e)
        layer_resp = None

    layer_arn = None
    if layer_resp:
        layer_arn = layer_resp.get('LayerVersionArn')
        print('Layer ARN:', layer_arn)

    print('Updating function code...')
    try:
        func_resp = update_function_code(layer_arn)
    except Exception as e:
        print('Failed to update function:', e)
        sys.exit(1)

    print('Done')
=======
import boto3
import sys
import json
from pathlib import Path

LAYER_ZIP = 'python.zip'
FUNCTION_ZIP = 'lambda_deploy.zip'
FUNCTION_NAME = 'ml-inference-slice-handler'
LAYER_NAME = 'mobilenetv3-python-deps'
RUNTIME = 'python3.10'

def publish_layer():
    if not Path(LAYER_ZIP).exists():
        print('Layer zip not found:', LAYER_ZIP)
        return None
    client = boto3.client('lambda')
    with open(LAYER_ZIP, 'rb') as f:
        resp = client.publish_layer_version(
            LayerName=LAYER_NAME,
            Content={'ZipFile': f.read()},
            CompatibleRuntimes=[RUNTIME],
            Description='Python dependencies for mobilenetv3 slices'
        )
    print('Published layer version:', resp.get('Version'))
    return resp


def update_function_code(layer_arn=None):
    if not Path(FUNCTION_ZIP).exists():
        print('Function zip not found:', FUNCTION_ZIP)
        return None
    client = boto3.client('lambda')
    with open(FUNCTION_ZIP, 'rb') as f:
        resp = client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=f.read(),
            Publish=True
        )
    print('Updated function code, status:', resp.get('LastUpdateStatus'))

    if layer_arn:
        # Get existing layers
        cfg = client.get_function_configuration(FunctionName=FUNCTION_NAME)
        existing_layers = [l['Arn'] for l in cfg.get('Layers', [])]
        # prepend new layer
        new_layers = [layer_arn] + [a for a in existing_layers if a != layer_arn]
        client.update_function_configuration(FunctionName=FUNCTION_NAME, Layers=new_layers)
        print('Updated function configuration with new layer')
    return resp


if __name__ == '__main__':
    print('Publishing layer...')
    try:
        layer_resp = publish_layer()
    except Exception as e:
        print('Failed to publish layer:', e)
        layer_resp = None

    layer_arn = None
    if layer_resp:
        layer_arn = layer_resp.get('LayerVersionArn')
        print('Layer ARN:', layer_arn)

    print('Updating function code...')
    try:
        func_resp = update_function_code(layer_arn)
    except Exception as e:
        print('Failed to update function:', e)
        sys.exit(1)

    print('Done')
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
