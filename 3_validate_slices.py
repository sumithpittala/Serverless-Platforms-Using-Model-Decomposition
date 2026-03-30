<<<<<<< HEAD
"""
Validation script to check if slices meet Serverless platform constraints.
Based on the research paper's Step 3: Check the decomposition.
"""
import onnx
import numpy as np
import os
from pathlib import Path

# Serverless platform constraints (from paper Table 1)
STEP_FUNCTIONS_PAYLOAD_LIMIT = 256 * 1024  # 256 KB
LAMBDA_MEMORY_LIMITS = [128, 256, 512, 1024, 1536, 2048, 3008, 10240]  # MB
LAMBDA_TEMP_STORAGE = 512 * 1024 * 1024  # 512 MB (default)
LAMBDA_DEPLOYMENT_SIZE = 50 * 1024 * 1024  # 50 MB direct upload, 250 MB via S3

def get_tensor_size_bytes(shape, dtype=np.float32):
    """Calculate tensor size in bytes."""
    dtype_size = np.dtype(dtype).itemsize
    total_elements = np.prod(shape) if shape else 1
    return int(total_elements * dtype_size)

def estimate_slice_memory(slice_path):
    """Estimate memory usage for a slice."""
    model = onnx.load(slice_path)
    
    # Estimate based on:
    # 1. Model weights (initializers)
    # 2. Intermediate activations
    # 3. Input/output tensors
    
    total_size = 0
    
    # Add initializer sizes
    for init in model.graph.initializer:
        shape = list(init.dims)
        dtype_size = 4  # Assume float32 (4 bytes)
        if init.data_type == onnx.TensorProto.FLOAT:
            dtype_size = 4
        elif init.data_type == onnx.TensorProto.FLOAT16:
            dtype_size = 2
        elif init.data_type == onnx.TensorProto.INT32:
            dtype_size = 4
        
        size = np.prod(shape) * dtype_size if shape else dtype_size
        total_size += size
    
    # Add input/output tensor sizes (rough estimate)
    for inp in model.graph.input:
        if inp.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in inp.type.tensor_type.shape.dim]
            total_size += get_tensor_size_bytes(shape)
    
    for out in model.graph.output:
        if out.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in out.type.tensor_type.shape.dim]
            total_size += get_tensor_size_bytes(shape)
    
    # Add overhead (ONNX Runtime, Python, etc.) - rough estimate
    overhead = 100 * 1024 * 1024  # 100 MB overhead
    
    return total_size + overhead

def check_slice_file_size(slice_path):
    """Check if slice file size is within deployment limits."""
    file_size = os.path.getsize(slice_path)
    return file_size, file_size <= LAMBDA_DEPLOYMENT_SIZE

def estimate_intermediate_payload_size(slice_path):
    """Estimate the size of intermediate payload between slices."""
    model = onnx.load(slice_path)
    
    # Estimate output tensor size
    max_output_size = 0
    for out in model.graph.output:
        if out.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in out.type.tensor_type.shape.dim]
            size = get_tensor_size_bytes(shape)
            max_output_size = max(max_output_size, size)
    
    # Add numpy array overhead
    overhead = 1024  # ~1 KB for numpy metadata
    return max_output_size + overhead

def validate_slices(slices_folder="slices", num_slices=5):
    """Validate all slices against Serverless constraints."""
    print("=" * 60)
    print("SLICE VALIDATION REPORT")
    print("=" * 60)
    print(f"\nConstraints:")
    print(f"  Step Functions payload limit: {STEP_FUNCTIONS_PAYLOAD_LIMIT / 1024:.1f} KB")
    print(f"  Lambda deployment size limit: {LAMBDA_DEPLOYMENT_SIZE / (1024*1024):.1f} MB")
    print(f"  Lambda temp storage: {LAMBDA_TEMP_STORAGE / (1024*1024):.1f} MB")
    print(f"  Lambda memory options: {LAMBDA_MEMORY_LIMITS} MB")
    
    all_valid = True
    max_payload_size = 0
    max_memory_needed = 0
    
    print(f"\n{'Slice':<10} {'File Size':<15} {'Est. Memory':<15} {'Payload Size':<15} {'Status':<10}")
    print("-" * 70)
    
    for i in range(num_slices):
        slice_path = f"{slices_folder}/slice_{i}.onnx"
        
        if not os.path.exists(slice_path):
            print(f"slice_{i:<6} {'MISSING':<70}")
            all_valid = False
            continue
        
        # Check file size
        file_size, file_ok = check_slice_file_size(slice_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Estimate memory
        est_memory = estimate_slice_memory(slice_path)
        est_memory_mb = est_memory / (1024 * 1024)
        max_memory_needed = max(max_memory_needed, est_memory_mb)
        
        # Estimate payload size (for intermediate outputs)
        payload_size = estimate_intermediate_payload_size(slice_path)
        max_payload_size = max(max_payload_size, payload_size)
        payload_ok = payload_size <= STEP_FUNCTIONS_PAYLOAD_LIMIT
        
        # Determine minimum Lambda memory needed
        min_lambda_memory = min([m for m in LAMBDA_MEMORY_LIMITS if m * 1024 * 1024 >= est_memory])
        
        # Status
        if file_ok and payload_ok:
            status = "✓ OK"
        else:
            status = "✗ FAIL"
            all_valid = False
            if not file_ok:
                status += " (file too large)"
            if not payload_ok:
                status += " (payload too large)"
        
        print(f"slice_{i:<6} {file_size_mb:>6.2f} MB    {est_memory_mb:>6.2f} MB    "
              f"{payload_size/1024:>6.2f} KB    {status:<10}")
    
    print("-" * 70)
    print(f"\nSummary:")
    print(f"  Maximum payload size: {max_payload_size / 1024:.2f} KB")
    print(f"  Maximum memory needed: {max_memory_needed:.2f} MB")
    print(f"  Recommended Lambda memory: {min([m for m in LAMBDA_MEMORY_LIMITS if m >= max_memory_needed])} MB")
    
    if max_payload_size > STEP_FUNCTIONS_PAYLOAD_LIMIT:
        print(f"\n⚠ WARNING: Payload size ({max_payload_size / 1024:.2f} KB) exceeds")
        print(f"  Step Functions limit ({STEP_FUNCTIONS_PAYLOAD_LIMIT / 1024:.1f} KB).")
        print(f"  Intermediate results MUST be stored in S3, not passed directly.")
        all_valid = False
    
    if all_valid:
        print(f"\n✓ All slices meet Serverless platform constraints!")
    else:
        print(f"\n✗ Some slices violate constraints. Consider:")
        print(f"  - Increasing the number of slices")
        print(f"  - Using S3 for all intermediate data (not just large payloads)")
        print(f"  - Optimizing model architecture")
    
    print("=" * 60)
    return all_valid

if __name__ == "__main__":
    import sys
    
    slices_folder = sys.argv[1] if len(sys.argv) > 1 else "slices"
    num_slices = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    validate_slices(slices_folder, num_slices)



=======
"""
Validation script to check if slices meet Serverless platform constraints.
Based on the research paper's Step 3: Check the decomposition.
"""
import onnx
import numpy as np
import os
from pathlib import Path

# Serverless platform constraints (from paper Table 1)
STEP_FUNCTIONS_PAYLOAD_LIMIT = 256 * 1024  # 256 KB
LAMBDA_MEMORY_LIMITS = [128, 256, 512, 1024, 1536, 2048, 3008, 10240]  # MB
LAMBDA_TEMP_STORAGE = 512 * 1024 * 1024  # 512 MB (default)
LAMBDA_DEPLOYMENT_SIZE = 50 * 1024 * 1024  # 50 MB direct upload, 250 MB via S3

def get_tensor_size_bytes(shape, dtype=np.float32):
    """Calculate tensor size in bytes."""
    dtype_size = np.dtype(dtype).itemsize
    total_elements = np.prod(shape) if shape else 1
    return int(total_elements * dtype_size)

def estimate_slice_memory(slice_path):
    """Estimate memory usage for a slice."""
    model = onnx.load(slice_path)
    
    # Estimate based on:
    # 1. Model weights (initializers)
    # 2. Intermediate activations
    # 3. Input/output tensors
    
    total_size = 0
    
    # Add initializer sizes
    for init in model.graph.initializer:
        shape = list(init.dims)
        dtype_size = 4  # Assume float32 (4 bytes)
        if init.data_type == onnx.TensorProto.FLOAT:
            dtype_size = 4
        elif init.data_type == onnx.TensorProto.FLOAT16:
            dtype_size = 2
        elif init.data_type == onnx.TensorProto.INT32:
            dtype_size = 4
        
        size = np.prod(shape) * dtype_size if shape else dtype_size
        total_size += size
    
    # Add input/output tensor sizes (rough estimate)
    for inp in model.graph.input:
        if inp.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in inp.type.tensor_type.shape.dim]
            total_size += get_tensor_size_bytes(shape)
    
    for out in model.graph.output:
        if out.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in out.type.tensor_type.shape.dim]
            total_size += get_tensor_size_bytes(shape)
    
    # Add overhead (ONNX Runtime, Python, etc.) - rough estimate
    overhead = 100 * 1024 * 1024  # 100 MB overhead
    
    return total_size + overhead

def check_slice_file_size(slice_path):
    """Check if slice file size is within deployment limits."""
    file_size = os.path.getsize(slice_path)
    return file_size, file_size <= LAMBDA_DEPLOYMENT_SIZE

def estimate_intermediate_payload_size(slice_path):
    """Estimate the size of intermediate payload between slices."""
    model = onnx.load(slice_path)
    
    # Estimate output tensor size
    max_output_size = 0
    for out in model.graph.output:
        if out.type.tensor_type.shape.dim:
            shape = [dim.dim_value if dim.dim_value > 0 else 1 
                    for dim in out.type.tensor_type.shape.dim]
            size = get_tensor_size_bytes(shape)
            max_output_size = max(max_output_size, size)
    
    # Add numpy array overhead
    overhead = 1024  # ~1 KB for numpy metadata
    return max_output_size + overhead

def validate_slices(slices_folder="slices", num_slices=5):
    """Validate all slices against Serverless constraints."""
    print("=" * 60)
    print("SLICE VALIDATION REPORT")
    print("=" * 60)
    print(f"\nConstraints:")
    print(f"  Step Functions payload limit: {STEP_FUNCTIONS_PAYLOAD_LIMIT / 1024:.1f} KB")
    print(f"  Lambda deployment size limit: {LAMBDA_DEPLOYMENT_SIZE / (1024*1024):.1f} MB")
    print(f"  Lambda temp storage: {LAMBDA_TEMP_STORAGE / (1024*1024):.1f} MB")
    print(f"  Lambda memory options: {LAMBDA_MEMORY_LIMITS} MB")
    
    all_valid = True
    max_payload_size = 0
    max_memory_needed = 0
    
    print(f"\n{'Slice':<10} {'File Size':<15} {'Est. Memory':<15} {'Payload Size':<15} {'Status':<10}")
    print("-" * 70)
    
    for i in range(num_slices):
        slice_path = f"{slices_folder}/slice_{i}.onnx"
        
        if not os.path.exists(slice_path):
            print(f"slice_{i:<6} {'MISSING':<70}")
            all_valid = False
            continue
        
        # Check file size
        file_size, file_ok = check_slice_file_size(slice_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Estimate memory
        est_memory = estimate_slice_memory(slice_path)
        est_memory_mb = est_memory / (1024 * 1024)
        max_memory_needed = max(max_memory_needed, est_memory_mb)
        
        # Estimate payload size (for intermediate outputs)
        payload_size = estimate_intermediate_payload_size(slice_path)
        max_payload_size = max(max_payload_size, payload_size)
        payload_ok = payload_size <= STEP_FUNCTIONS_PAYLOAD_LIMIT
        
        # Determine minimum Lambda memory needed
        min_lambda_memory = min([m for m in LAMBDA_MEMORY_LIMITS if m * 1024 * 1024 >= est_memory])
        
        # Status
        if file_ok and payload_ok:
            status = "✓ OK"
        else:
            status = "✗ FAIL"
            all_valid = False
            if not file_ok:
                status += " (file too large)"
            if not payload_ok:
                status += " (payload too large)"
        
        print(f"slice_{i:<6} {file_size_mb:>6.2f} MB    {est_memory_mb:>6.2f} MB    "
              f"{payload_size/1024:>6.2f} KB    {status:<10}")
    
    print("-" * 70)
    print(f"\nSummary:")
    print(f"  Maximum payload size: {max_payload_size / 1024:.2f} KB")
    print(f"  Maximum memory needed: {max_memory_needed:.2f} MB")
    print(f"  Recommended Lambda memory: {min([m for m in LAMBDA_MEMORY_LIMITS if m >= max_memory_needed])} MB")
    
    if max_payload_size > STEP_FUNCTIONS_PAYLOAD_LIMIT:
        print(f"\n⚠ WARNING: Payload size ({max_payload_size / 1024:.2f} KB) exceeds")
        print(f"  Step Functions limit ({STEP_FUNCTIONS_PAYLOAD_LIMIT / 1024:.1f} KB).")
        print(f"  Intermediate results MUST be stored in S3, not passed directly.")
        all_valid = False
    
    if all_valid:
        print(f"\n✓ All slices meet Serverless platform constraints!")
    else:
        print(f"\n✗ Some slices violate constraints. Consider:")
        print(f"  - Increasing the number of slices")
        print(f"  - Using S3 for all intermediate data (not just large payloads)")
        print(f"  - Optimizing model architecture")
    
    print("=" * 60)
    return all_valid

if __name__ == "__main__":
    import sys
    
    slices_folder = sys.argv[1] if len(sys.argv) > 1 else "slices"
    num_slices = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    validate_slices(slices_folder, num_slices)



>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
