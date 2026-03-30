"""
Complete pipeline script: Export model -> Slice -> Validate -> Upload -> Deploy
"""
import subprocess
import sys
import os

def run_step(step_name, script_name, description):
    """Run a pipeline step."""
    print("\n" + "=" * 60)
    print(f"STEP: {step_name}")
    print("=" * 60)
    print(description)
    print("-" * 60)
    
    if not os.path.exists(script_name):
        print(f"✗ Script {script_name} not found, skipping...")
        return False
    
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"✓ {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {step_name} failed with error: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Python script {script_name} not found")
        return False

def main():
    """Run the complete pipeline."""
    print("=" * 60)
    print("ML INFERENCE SERVERLESS PIPELINE")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Export TensorFlow model to ONNX")
    print("  2. Slice the ONNX model into sub-models")
    print("  3. Validate slices against Serverless constraints")
    print("  4. Upload slices to S3 (optional)")
    print("  5. Deploy Lambda function (optional)")
    print("  6. Deploy Step Functions workflow (optional)")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    steps = [
        ("Export to ONNX", "1_export_to_onnx.py", 
         "Converting MobileNetV3 to ONNX format"),
        ("Slice Model", "2_slice_model.py",
         "Decomposing ONNX model into 5 slices"),
        ("Validate Slices", "3_validate_slices.py",
         "Checking slices against Serverless constraints"),
    ]
    
    optional_steps = [
        ("Upload to S3", "upload_slices_to_s3.py",
         "Uploading slices to S3 bucket (requires AWS credentials)"),
        ("Deploy Lambda", "deploy_lambda.py",
         "Deploying Lambda function (requires AWS credentials)"),
        ("Deploy Step Functions", "deploy_step_functions.py",
         "Deploying Step Functions workflow (requires AWS credentials)"),
    ]
    
    # Run required steps
    for step_name, script, description in steps:
        if not run_step(step_name, script, description):
            print(f"\n✗ Pipeline failed at step: {step_name}")
            return
    
    # Ask about optional steps
    print("\n" + "=" * 60)
    print("OPTIONAL DEPLOYMENT STEPS")
    print("=" * 60)
    
    for step_name, script, description in optional_steps:
        response = input(f"\nRun {step_name}? (y/n): ")
        if response.lower() == 'y':
            if not run_step(step_name, script, description):
                print(f"⚠ {step_name} failed, but continuing...")
    
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Test the Lambda function locally")
    print("  2. Start a Step Functions execution")
    print("  3. Monitor execution in AWS Console")

if __name__ == "__main__":
    main()



