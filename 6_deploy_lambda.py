import os
import shutil
import subprocess
import zipfile
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

# Configuration
LAMBDA_FUNCTION_NAME = "ml-inference-slice-handler"
LAMBDA_ROLE_NAME = "ml-inference-lambda-role"
LAMBDA_HANDLER = "handler.lambda_handler"
LAMBDA_RUNTIME = "python3.10"
LAMBDA_MEMORY = 3008 
LAMBDA_TIMEOUT = 900
LOCALSTACK_URL = "http://localhost:4566"

def get_client(service):
    """Helper to get a LocalStack-targeted boto3 client."""
    return boto3.client(
        service,
        endpoint_url=LOCALSTACK_URL,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1"
    )

def create_deployment_package():
    """Create deployment package for Lambda."""
    print("Creating Lambda deployment package...")
    package_dir = "lambda_package"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy your inference handler
    if not os.path.exists("handler.py"):
        print("Error: handler.py not found in current directory!")
        exit(1)
    shutil.copy("handler.py", package_dir)
    
    # Install Linux-compatible binaries
    print("Installing dependencies (numpy, onnxruntime)...")
    subprocess.run([
        "pip", "install", "numpy", "onnxruntime", 
        "-t", package_dir, 
        "--platform", "manylinux2014_x86_64",
        "--only-binary", ":all:", 
        "--python-version", "3.10"
    ], check=True)
    
    zip_path = "lambda_deployment.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    print(f"✓ Package created: {zip_path}")
    return zip_path

def create_iam_role():
    """Create IAM role in LocalStack."""
    print("\nSetting up IAM role...")
    iam = get_client('iam')
    trust_policy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    
    try:
        role = iam.create_role(RoleName=LAMBDA_ROLE_NAME, AssumeRolePolicyDocument=trust_policy)
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            return iam.get_role(RoleName=LAMBDA_ROLE_NAME)['Role']['Arn']
        raise

def deploy_lambda(zip_path, role_arn):
    """Deploy function by uploading to S3 first to bypass 50MB direct upload limit."""
    print("\nDeploying Lambda function via S3...")
    lmb = get_client('lambda')
    s3 = get_client('s3')
    
    bucket_name = "lambda-deploy-bucket"
    zip_key = "lambda_deployment.zip"

    # Ensure deployment bucket exists
    try:
        s3.create_bucket(Bucket=bucket_name)
    except:
        pass

    print(f"Uploading {zip_path} to S3 bucket '{bucket_name}'...")
    s3.upload_file(zip_path, bucket_name, zip_key)

    try:
        lmb.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
        lmb.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            S3Bucket=bucket_name,
            S3Key=zip_key
        )
        print(f"✓ Updated function from S3: {LAMBDA_FUNCTION_NAME}")
    except ClientError:
        lmb.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Role=role_arn,
            Handler=LAMBDA_HANDLER,
            Code={'S3Bucket': bucket_name, 'S3Key': zip_key},
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY
        )
        print(f"✓ Created new function from S3: {LAMBDA_FUNCTION_NAME}")

def main():
    """The main entry point for the deployment process."""
    print("=" * 60)
    print("LOCALSTACK LAMBDA DEPLOYMENT (S3-BASED)")
    print("=" * 60)
    
    try:
        # Step 1: Zip the code and dependencies
        zip_path = create_deployment_package()
        
        # Step 2: Set up permissions
        role_arn = create_iam_role()
        
        # Step 3: Deploy using S3 to handle large package size
        deploy_lambda(zip_path, role_arn)
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")

if __name__ == "__main__":
    main()