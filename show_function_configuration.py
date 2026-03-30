import boto3

FUNCTION_NAME = 'MobileNetV3Lambda'
client = boto3.client('lambda')

conf = client.get_function_configuration(FunctionName=FUNCTION_NAME)
print('FunctionName:', conf.get('FunctionName'))
print('Handler:', conf.get('Handler'))
print('Runtime:', conf.get('Runtime'))
print('Role:', conf.get('Role'))
print('Layers:', [l.get('Arn') for l in conf.get('Layers') or []])
print('LastUpdateStatus:', conf.get('LastUpdateStatus'))
print('Description:', conf.get('Description'))
print('Environment:', conf.get('Environment'))
