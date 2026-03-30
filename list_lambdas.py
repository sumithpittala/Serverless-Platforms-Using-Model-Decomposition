<<<<<<< HEAD
<<<<<<< HEAD
import boto3
from botocore.exceptions import ClientError

client = boto3.client('lambda')

print('Listing Lambda functions (first 200):')
try:
    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page.get('Functions', []):
            name = fn.get('FunctionName')
            arn = fn.get('FunctionArn')
            runtime = fn.get('Runtime')
            lm = fn.get('LastModified')
            layers = fn.get('Layers') or []
            layer_arns = [l.get('Arn') for l in layers]
            print(f"- {name} | {arn} | runtime={runtime} | last_modified={lm} | layers={layer_arns}")
except ClientError as e:
    print('AWS error listing functions:', e)
except Exception as e:
    print('Error:', e)
=======
import boto3
from botocore.exceptions import ClientError

client = boto3.client('lambda')

print('Listing Lambda functions (first 200):')
try:
    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page.get('Functions', []):
            name = fn.get('FunctionName')
            arn = fn.get('FunctionArn')
            runtime = fn.get('Runtime')
            lm = fn.get('LastModified')
            layers = fn.get('Layers') or []
            layer_arns = [l.get('Arn') for l in layers]
            print(f"- {name} | {arn} | runtime={runtime} | last_modified={lm} | layers={layer_arns}")
except ClientError as e:
    print('AWS error listing functions:', e)
except Exception as e:
    print('Error:', e)
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
=======
import boto3
from botocore.exceptions import ClientError

client = boto3.client('lambda')

print('Listing Lambda functions (first 200):')
try:
    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        for fn in page.get('Functions', []):
            name = fn.get('FunctionName')
            arn = fn.get('FunctionArn')
            runtime = fn.get('Runtime')
            lm = fn.get('LastModified')
            layers = fn.get('Layers') or []
            layer_arns = [l.get('Arn') for l in layers]
            print(f"- {name} | {arn} | runtime={runtime} | last_modified={lm} | layers={layer_arns}")
except ClientError as e:
    print('AWS error listing functions:', e)
except Exception as e:
    print('Error:', e)
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
