import subprocess
import sys
import os
import time
from pathlib import Path

# --- CONFIGURATION ---
MODEL_NAME = "mobilenetv3.onnx"
SLICES_DIR = "slices"
BUCKET_NAME = "mobilenetv3-bucket"
TEST_IMAGE = "dog.jpg"

def print_header(text):
    print("\n" + "=" * 65)
    print(f" {text}")
    print("=" * 65)

def check_localstack():
    """Verify LocalStack is running before starting."""
    import urllib.request
    print("Checking LocalStack status...")
    try:
        urllib.request.urlopen("http://localhost:4566/_localstack/health", timeout=2)
        print("✓ LocalStack is ONLINE")
    except Exception:
        print("✗ ERROR: LocalStack is OFFLINE. Please run 'docker-compose up -d' first.")
        sys.exit(1)

def run_command(cmd, step_desc):
    """Executes a shell command and monitors success."""
    print(f"\n▶ STARTING: {step_desc}")
    print(f"Command: {' '.join(cmd)}")
    try:
        # We use subprocess.run to show output in real-time
        result = subprocess.run(cmd, check=True)
        print(f"✓ SUCCESS: {step_desc}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ FAILED: {step_desc} (Error Code: {e.returncode})")
        return False

def main():
    print_header("SERVERLESS ML DECOMPOSITION PIPELINE")
    
    # 0. Infrastructure Check
    check_localstack()
    
    # Ensure local slices directory exists
    Path(SLICES_DIR).mkdir(exist_ok=True)

    # Define the execution sequence
    pipeline_steps = [
        {
            "name": "Export Model",
            "script": "1_export_to_onnx.py",
            "args": []
        },
        {
            "name": "Slice Model",
            "script": "2_slice_model.py",
            "args": ["--model", MODEL_NAME, "--slices", "5", "--out_dir", SLICES_DIR]
        },
        {
            "name": "Validate Slices",
            "script": "3_validate_slices.py",
            "args": []
        },
        {
            "name": "Prepare & Upload Input",
            "script": "4_create_input_and_upload.py",
            "args": ["--image", TEST_IMAGE, "--upload"]
        },
        {
            "name": "Upload Slices to S3",
            "script": "5_create_s3_manifest.py",
            "args": ["--bucket", BUCKET_NAME]
        },
        {
            "name": "Deploy Lambda Function",
            "script": "6_deploy_lambda.py",
            "args": []
        },
        {
            "name": "Deploy Step Functions",
            "script": "7_deploy_step_functions.py",
            "args": []
        }
    ]

    # Execute Steps
    start_time = time.time()
    
    for step in pipeline_steps:
        script_path = step["script"]
        
        if not os.path.exists(script_path):
            print(f"✗ Skipping '{step['name']}': {script_path} not found.")
            continue

        cmd = [sys.executable, script_path] + step["args"]
        
        if not run_command(cmd, step["name"]):
            print_header("PIPELINE ABORTED")
            print(f"The process failed at: {step['name']}")
            return

    duration = time.time() - start_time
    print_header("PIPELINE COMPLETE")
    print(f"Total Execution Time: {duration:.2f} seconds")
    print("\nNext Steps for Demo:")
    print(f"1. Check S3: awslocal s3 ls s3://{BUCKET_NAME} --recursive")
    print(f"2. Check State Machine: awslocal stepfunctions list-state-machines")
    print(f"3. Trigger Inference via terminal or Step Functions UI")

if __name__ == "__main__":
    main()