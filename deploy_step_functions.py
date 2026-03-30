"""
Deploy AWS Step Functions state machine for ML inference workflow.
"""
import boto3
import json

STEP_FUNCTIONS_NAME = "ml-inference-workflow"
LAMBDA_FUNCTION_NAME = "ml-inference-slice-handler"

def get_lambda_arn(function_name):
    """Get Lambda function ARN."""
    lambda_client = boto3.client('lambda')
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except Exception as e:
        print(f"✗ Error: Lambda function {function_name} not found")
        print(f"  Run deploy_lambda.py first")
        raise

def create_iam_role_for_step_functions():
    """Create IAM role for Step Functions."""
    print("Creating IAM role for Step Functions...")
    iam = boto3.client('iam')
    
    role_name = "ml-inference-stepfunctions-role"
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "states.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Get Lambda function ARN
    lambda_arn = get_lambda_arn(LAMBDA_FUNCTION_NAME)
    
    # Policy for Step Functions to invoke Lambda
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": lambda_arn
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for ML inference Step Functions workflow"
        )
        print(f"✓ Created role: {role_name}")
        
        # Attach policy
        policy_name = f"{role_name}-policy"
        policy = iam.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document)
        )
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy['Policy']['Arn']
        )
        print(f"✓ Attached policy: {policy_name}")
        
        return role['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role {role_name} already exists, fetching ARN...")
        role = iam.get_role(RoleName=role_name)
        return role['Role']['Arn']

def load_state_machine_definition():
    """Load Step Functions state machine definition."""
    # Try JSON first, then YAML
    for filename in ["step_functions_definition.json", "step_functions_definition.yaml"]:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                if filename.endswith('.json'):
                    return json.load(f)
                else:
                    # For YAML, you'd need pyyaml, but we'll use JSON
                    pass
    
    # Fallback: use JSON directly
    with open("step_functions_definition.json", 'r') as f:
        return json.load(f)

def deploy_step_functions(role_arn):
    """Deploy or update Step Functions state machine."""
    print("\nDeploying Step Functions state machine...")
    sfn = boto3.client('stepfunctions')
    
    # Load definition
    definition = load_state_machine_definition()
    
    # Update Lambda function name in definition
    lambda_arn = get_lambda_arn(LAMBDA_FUNCTION_NAME)
    
    # Update the definition to use the actual Lambda ARN
    # The definition uses FunctionName, but we can also use ARN
    definition_str = json.dumps(definition)
    definition_str = definition_str.replace(
        f'"FunctionName": "{LAMBDA_FUNCTION_NAME}"',
        f'"FunctionName": "{lambda_arn}"'
    )
    definition = json.loads(definition_str)
    
    try:
        # Try to update existing state machine
        response = sfn.update_state_machine(
            stateMachineArn=f"arn:aws:states:us-east-1:ACCOUNT_ID:stateMachine:{STEP_FUNCTIONS_NAME}",
            definition=json.dumps(definition),
            roleArn=role_arn
        )
        print(f"✓ Updated state machine: {STEP_FUNCTIONS_NAME}")
        return response['stateMachineArn']
    except:
        # Create new state machine
        response = sfn.create_state_machine(
            name=STEP_FUNCTIONS_NAME,
            definition=json.dumps(definition),
            roleArn=role_arn,
            type='STANDARD',
            loggingConfiguration={
                'level': 'ALL',
                'includeExecutionData': True
            }
        )
        print(f"✓ Created state machine: {STEP_FUNCTIONS_NAME}")
        return response['stateMachineArn']

def main():
    """Main deployment function."""
    import os
    
    print("=" * 60)
    print("STEP FUNCTIONS DEPLOYMENT")
    print("=" * 60)
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print("✗ Error: AWS credentials not configured")
        print(f"  {e}")
        return
    
    # Create IAM role
    role_arn = create_iam_role_for_step_functions()
    
    # Deploy state machine
    state_machine_arn = deploy_step_functions(role_arn)
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\nState Machine Name: {STEP_FUNCTIONS_NAME}")
    print(f"State Machine ARN: {state_machine_arn}")
    print(f"\nTo start an execution, use:")
    print(f"  aws stepfunctions start-execution \\")
    print(f"    --state-machine-arn {state_machine_arn} \\")
    print(f"    --input '{{\"bucket\":\"mobilenetv3-bucket\",\"total_slices\":5,\"input_key\":\"mobilenetv3/input.npy\",\"output_key\":\"mobilenetv3/output.npy\",\"model_prefix\":\"mobilenetv3/slices\"}}'")

if __name__ == "__main__":
    main()



