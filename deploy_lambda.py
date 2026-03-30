<<<<<<< HEAD
"""
Deploy Lambda function for ML inference slices.
Packages the handler and dependencies for AWS Lambda deployment.
"""
import os
import shutil
import subprocess
import zipfile
import boto3
from pathlib import Path

LAMBDA_FUNCTION_NAME = "ml-inference-slice-handler"
LAMBDA_ROLE_NAME = "ml-inference-lambda-role"
LAMBDA_HANDLER = "handler.lambda_handler"
LAMBDA_RUNTIME = "python3.10"
LAMBDA_MEMORY = 3008  # MB (max for better performance)
LAMBDA_TIMEOUT = 900  # 15 minutes (max)

def create_deployment_package():
    """Create deployment package for Lambda."""
    print("Creating Lambda deployment package...")
    
    # Create temporary directory
    package_dir = "lambda_package"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy handler
    shutil.copy("handler.py", package_dir)
    
    # Install dependencies
    print("Installing dependencies...")
    requirements = [
        "boto3",
        "numpy",
        "onnxruntime"
    ]
    
    # Create requirements.txt
    with open(f"{package_dir}/requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    # Install to package directory
    subprocess.run([
        "pip", "install", "-r", f"{package_dir}/requirements.txt",
        "-t", package_dir, "--platform", "linux_x86_64",
        "--only-binary", ":all:", "--python-version", "3.10"
    ], check=True)
    
    # Create zip file
    zip_path = "lambda_deployment.zip"
    print(f"Creating {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    file_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✓ Package created: {zip_path} ({file_size:.2f} MB)")
    
    return zip_path

def create_iam_role():
    """Create IAM role for Lambda function."""
    print("\nCreating IAM role...")
    iam = boto3.client('iam')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Policy for Lambda execution and S3 access
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::mobilenetv3-bucket/*"
            }
        ]
    }
    
    try:
        # Create role
        role = iam.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=str(trust_policy).replace("'", '"'),
            Description="Role for ML inference Lambda function"
        )
        print(f"✓ Created role: {LAMBDA_ROLE_NAME}")
        
        # Attach policy
        policy_name = f"{LAMBDA_ROLE_NAME}-policy"
        policy = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=str(policy_document).replace("'", '"')
        )
        iam.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn=policy['Policy']['Arn']
        )
        print(f"✓ Attached policy: {policy_name}")
        
        return role['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role {LAMBDA_ROLE_NAME} already exists, fetching ARN...")
        role = iam.get_role(RoleName=LAMBDA_ROLE_NAME)
        return role['Role']['Arn']

def deploy_lambda(zip_path, role_arn):
    """Deploy or update Lambda function."""
    print("\nDeploying Lambda function...")
    lambda_client = boto3.client('lambda')
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        print(f"✓ Updated function: {LAMBDA_FUNCTION_NAME}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            MemorySize=LAMBDA_MEMORY,
            Timeout=LAMBDA_TIMEOUT,
            Handler=LAMBDA_HANDLER,
            Runtime=LAMBDA_RUNTIME
        )
        print(f"✓ Updated configuration")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Role=role_arn,
            Handler=LAMBDA_HANDLER,
            Code={'ZipFile': zip_content},
            Description="ML inference handler for ONNX model slices",
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={
                'Variables': {}
            }
        )
        print(f"✓ Created function: {LAMBDA_FUNCTION_NAME}")
    
    print(f"✓ Function ARN: {response['FunctionArn']}")
    return response['FunctionArn']

def main():
    """Main deployment function."""
    print("=" * 60)
    print("LAMBDA DEPLOYMENT")
    print("=" * 60)
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print("✗ Error: AWS credentials not configured")
        print(f"  {e}")
        return
    
    # Create deployment package
    zip_path = create_deployment_package()
    
    # Create IAM role
    role_arn = create_iam_role()
    
    # Deploy Lambda
    function_arn = deploy_lambda(zip_path, role_arn)
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\nFunction Name: {LAMBDA_FUNCTION_NAME}")
    print(f"Function ARN: {function_arn}")
    print(f"Role ARN: {role_arn}")
    print(f"\nNext steps:")
    print(f"  1. Upload model slices to S3")
    print(f"  2. Create Step Functions state machine")
    print(f"  3. Test the workflow")

if __name__ == "__main__":
    main()



=======
"""
Deploy Lambda function for ML inference slices.
Packages the handler and dependencies for AWS Lambda deployment.
"""
import os
import shutil
import subprocess
import zipfile
import boto3
from pathlib import Path

LAMBDA_FUNCTION_NAME = "ml-inference-slice-handler"
LAMBDA_ROLE_NAME = "ml-inference-lambda-role"
LAMBDA_HANDLER = "handler.lambda_handler"
LAMBDA_RUNTIME = "python3.10"
LAMBDA_MEMORY = 3008  # MB (max for better performance)
LAMBDA_TIMEOUT = 900  # 15 minutes (max)

def create_deployment_package():
    """Create deployment package for Lambda."""
    print("Creating Lambda deployment package...")
    
    # Create temporary directory
    package_dir = "lambda_package"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy handler
    shutil.copy("handler.py", package_dir)
    
    # Install dependencies
    print("Installing dependencies...")
    requirements = [
        "boto3",
        "numpy",
        "onnxruntime"
    ]
    
    # Create requirements.txt
    with open(f"{package_dir}/requirements.txt", "w") as f:
        f.write("\n".join(requirements))
    
    # Install to package directory
    subprocess.run([
        "pip", "install", "-r", f"{package_dir}/requirements.txt",
        "-t", package_dir, "--platform", "linux_x86_64",
        "--only-binary", ":all:", "--python-version", "3.10"
    ], check=True)
    
    # Create zip file
    zip_path = "lambda_deployment.zip"
    print(f"Creating {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    file_size = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✓ Package created: {zip_path} ({file_size:.2f} MB)")
    
    return zip_path

def create_iam_role():
    """Create IAM role for Lambda function."""
    print("\nCreating IAM role...")
    iam = boto3.client('iam')
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Policy for Lambda execution and S3 access
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::mobilenetv3-bucket/*"
            }
        ]
    }
    
    try:
        # Create role
        role = iam.create_role(
            RoleName=LAMBDA_ROLE_NAME,
            AssumeRolePolicyDocument=str(trust_policy).replace("'", '"'),
            Description="Role for ML inference Lambda function"
        )
        print(f"✓ Created role: {LAMBDA_ROLE_NAME}")
        
        # Attach policy
        policy_name = f"{LAMBDA_ROLE_NAME}-policy"
        policy = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=str(policy_document).replace("'", '"')
        )
        iam.attach_role_policy(
            RoleName=LAMBDA_ROLE_NAME,
            PolicyArn=policy['Policy']['Arn']
        )
        print(f"✓ Attached policy: {policy_name}")
        
        return role['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role {LAMBDA_ROLE_NAME} already exists, fetching ARN...")
        role = iam.get_role(RoleName=LAMBDA_ROLE_NAME)
        return role['Role']['Arn']

def deploy_lambda(zip_path, role_arn):
    """Deploy or update Lambda function."""
    print("\nDeploying Lambda function...")
    lambda_client = boto3.client('lambda')
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=LAMBDA_FUNCTION_NAME,
            ZipFile=zip_content
        )
        print(f"✓ Updated function: {LAMBDA_FUNCTION_NAME}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_FUNCTION_NAME,
            MemorySize=LAMBDA_MEMORY,
            Timeout=LAMBDA_TIMEOUT,
            Handler=LAMBDA_HANDLER,
            Runtime=LAMBDA_RUNTIME
        )
        print(f"✓ Updated configuration")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=LAMBDA_FUNCTION_NAME,
            Runtime=LAMBDA_RUNTIME,
            Role=role_arn,
            Handler=LAMBDA_HANDLER,
            Code={'ZipFile': zip_content},
            Description="ML inference handler for ONNX model slices",
            Timeout=LAMBDA_TIMEOUT,
            MemorySize=LAMBDA_MEMORY,
            Environment={
                'Variables': {}
            }
        )
        print(f"✓ Created function: {LAMBDA_FUNCTION_NAME}")
    
    print(f"✓ Function ARN: {response['FunctionArn']}")
    return response['FunctionArn']

def main():
    """Main deployment function."""
    print("=" * 60)
    print("LAMBDA DEPLOYMENT")
    print("=" * 60)
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print("✗ Error: AWS credentials not configured")
        print(f"  {e}")
        return
    
    # Create deployment package
    zip_path = create_deployment_package()
    
    # Create IAM role
    role_arn = create_iam_role()
    
    # Deploy Lambda
    function_arn = deploy_lambda(zip_path, role_arn)
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\nFunction Name: {LAMBDA_FUNCTION_NAME}")
    print(f"Function ARN: {function_arn}")
    print(f"Role ARN: {role_arn}")
    print(f"\nNext steps:")
    print(f"  1. Upload model slices to S3")
    print(f"  2. Create Step Functions state machine")
    print(f"  3. Test the workflow")

if __name__ == "__main__":
    main()



>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
