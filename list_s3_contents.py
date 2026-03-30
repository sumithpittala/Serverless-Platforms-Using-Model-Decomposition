import boto3
s3 = boto3.client('s3')
resp = s3.list_objects_v2(Bucket='mobilenetv3-bucket', Prefix='mobilenetv3/')
print('Found:', resp.get('KeyCount'))
for obj in resp.get('Contents', []):
    print('-', obj['Key'], obj['Size'])
