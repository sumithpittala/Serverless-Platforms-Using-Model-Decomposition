"""
Deploy Step Functions state machine for ML inference workflow to LocalStack.
"""
import boto3
import json
import os
from botocore.exceptions import ClientError

# Configuration
STEP_FUNCTIONS_NAME = "ml-inference-workflow"
LAMBDA_FUNCTION_NAME = "ml-inference-slice-handler"
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

def get_lambda_arn(function_name):
    """Get Lambda function ARN from LocalStack."""
    lmb = get_client('lambda')
    try:
        response = lmb.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception:
        print(f"✗ Error: Lambda function {function_name} not found. Run deploy_lambda.py first!")
        raise

def create_iam_role_for_step_functions():
    """Create IAM role for Step Functions in LocalStack."""
    print("Setting up IAM role for Step Functions...")
    iam = get_client('iam')
    role_name = "ml-inference-stepfunctions-role"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"Service": "states.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }

    try:
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        print(f"✓ Created role: {role_name}")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            return iam.get_role(RoleName=role_name)['Role']['Arn']
        raise

def load_state_machine_definition():
    """Load Step Functions state machine definition from JSON file."""
    filename = "step_functions_definition.json"
    if not os.path.exists(filename):
        # Create a basic fallback definition if file is missing
        print(f"! {filename} not found, using a default definition...")
        return {
            "StartAt": "ProcessSlice",
            "States": {
                "ProcessSlice": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:us-east-1:000000000000:function:ml-inference-slice-handler",
                    "End": True
                }
            }
        }
    with open(filename, 'r') as f:
        return json.load(f)

def deploy_step_functions(role_arn):
    """Deploy or update Step Functions state machine in LocalStack."""
    print("\nDeploying Step Functions state machine...")
    sfn = get_client('stepfunctions')
    
    definition = load_state_machine_definition()
    lambda_arn = get_lambda_arn(LAMBDA_FUNCTION_NAME)
    
    # Inject the actual Lambda ARN into the definition string
    definition_str = json.dumps(definition)
    # This assumes your JSON uses the Lambda name as a placeholder
    definition_str = definition_str.replace(LAMBDA_FUNCTION_NAME, lambda_arn)
    
    # In LocalStack, the account ID is usually 000000000000
    state_machine_arn = f"arn:aws:states:us-east-1:000000000000:stateMachine:{STEP_FUNCTIONS_NAME}"
    
    try:
        # Check if it exists
        sfn.describe_state_machine(stateMachineArn=state_machine_arn)
        sfn.update_state_machine(
            stateMachineArn=state_machine_arn,
            definition=definition_str,
            roleArn=role_arn
        )
        print(f"✓ Updated state machine: {STEP_FUNCTIONS_NAME}")
    except ClientError:
        # Create new
        response = sfn.create_state_machine(
            name=STEP_FUNCTIONS_NAME,
            definition=definition_str,
            roleArn=role_arn,
            type='STANDARD'
        )
        state_machine_arn = response['stateMachineArn']
        print(f"✓ Created state machine: {STEP_FUNCTIONS_NAME}")
        
    return state_machine_arn

def main():
    print("=" * 60)
    print("LOCALSTACK STEP FUNCTIONS DEPLOYMENT")
    print("=" * 60)
    
    try:
        # 1. Ensure Step Functions is enabled in LocalStack
        sts = get_client('sts')
        sts.get_caller_identity()
        
        # 2. Get/Create Role
        role_arn = create_iam_role_for_step_functions()
        
        # 3. Deploy
        sm_arn = deploy_step_functions(role_arn)
        
        print("\nDEPLOYMENT COMPLETE")
        print(f"ARN: {sm_arn}")
        print("\nTo test execution:")
        print(f"awslocal stepfunctions start-execution --state-machine-arn {sm_arn} --input '{{}}'")
    except Exception as e:
        print(f"✗ Deployment failed: {e}")

if __name__ == "__main__":
    main()