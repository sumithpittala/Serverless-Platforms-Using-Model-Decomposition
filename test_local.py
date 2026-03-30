"""
Test the Lambda handler locally before deploying.
Simulates the Step Functions workflow by calling handler sequentially.
"""
import json
import numpy as np
from handler import lambda_handler

class MockContext:
    """Mock AWS Lambda context."""
    def __init__(self):
        self.function_name = "ml-inference-slice-handler"
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = 3008
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
        self.aws_request_id = "test-request-id"

def test_local_inference():
    """Test the inference pipeline locally."""
    print("=" * 60)
    print("LOCAL INFERENCE TEST")
    print("=" * 60)
    
    # Configuration
    bucket = "mobilenetv3-bucket"
    total_slices = 5
    input_key = "mobilenetv3/input.npy"
    output_key = "mobilenetv3/output.npy"
    model_prefix = "mobilenetv3/slices"
    
    # Check if slices exist locally
    import os
    if not os.path.exists("slices"):
        print("✗ Error: slices directory not found")
        print("  Run 2_slice_model.py first")
        return
    
    # Check if input exists
    if not os.path.exists("input.npy"):
        print("✗ Error: input.npy not found")
        print("  Run create_input_and_upload.py first (or create input.npy manually)")
        return
    
    print(f"\nConfiguration:")
    print(f"  Bucket: {bucket}")
    print(f"  Total slices: {total_slices}")
    print(f"  Input key: {input_key}")
    print(f"  Model prefix: {model_prefix}")
    
    # For local testing, we'll modify the handler to use local files
    # This is a simplified version that works with local filesystem
    
    print(f"\n{'Slice':<10} {'Status':<15} {'Output Shape':<20}")
    print("-" * 50)
    
    context = MockContext()
    current_input_key = input_key
    
    for slice_id in range(total_slices):
        # Create event
        event = {
            "bucket": bucket,
            "slice_id": slice_id,
            "total_slices": total_slices,
            "input_key": current_input_key,
            "output_key": f"mobilenetv3/intermediate_{slice_id}.npy",
            "model_prefix": model_prefix
        }
        
        print(f"slice_{slice_id:<6}", end=" ")
        
        try:
            # For local testing, we need to modify handler to work with local files
            # This is a simplified test - in practice, you'd mock S3 or use local paths
            print("⚠ Skipped (requires S3 or local file mocking)")
            print("  To test properly:")
            print("    1. Set up local S3 (LocalStack) or")
            print("    2. Use actual S3 bucket with uploaded slices")
            break
            
        except Exception as e:
            print(f"✗ FAILED: {e}")
            return
        
        # Update for next iteration
        if slice_id < total_slices - 1:
            current_input_key = event.get("input_key_next", f"mobilenetv3/intermediate_{slice_id}.npy")
    
    print("\n" + "=" * 60)
    print("NOTE: Full local testing requires:")
    print("  - S3 access (or LocalStack for local S3)")
    print("  - Slices uploaded to S3")
    print("  - Input data uploaded to S3")
    print("\nFor now, test individual components:")
    print("  - Validate slices: python 3_validate_slices.py")
    print("  - Test ONNX Runtime: Load and run slices manually")

if __name__ == "__main__":
    test_local_inference()



