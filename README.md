[README.md](https://github.com/user-attachments/files/26353867/README.md)
# mobilenetv3 serverless prototype

This project demonstrates the paper "Machine Learning Inference on Serverless Platforms Using Model Decomposition" by slicing an ONNX model and running each slice as a separate Serverless function (prototype used AWS Lambda + Step Functions).

Quick tasks to run locally:

- Extract the included research paper text (requires `onnxenv` venv):

```powershell
& .\onnxenv\Scripts\Activate.ps1
python -c "import fitz; d=fitz.open('IOMP RP.pdf'); print(d[0].get_text()[:500])"
```

- Create input and optionally upload to S3:

```powershell
python create_input_and_upload.py --image dog.jpg --out input.npy --upload --bucket <my-bucket> --key mobilenetv3/input.npy
```

- Upload model slices to S3:

```powershell
python upload_slices_to_s3.py --bucket <my-bucket> --prefix mobilenetv3/slices/
```

Notes:
- `handler.py` implements a Lambda-like handler expecting events with keys: `bucket`, `slice_id`, `total_slices`, `input_key`, `output_key`.
- Slices live in `slices/slice_*.onnx` after running `2_slice_model.py`.
# Machine Learning Inference on Serverless Platforms

This project implements the methodology from the research paper: **"Machine Learning Inference on Serverless Platforms Using Model Decomposition"** (UCC '23).

## Overview

The project decomposes large ML models into smaller sub-models (slices) that can be executed sequentially on AWS Lambda functions, orchestrated by AWS Step Functions. This approach overcomes Serverless platform limitations such as:
- Deployment package size limits
- Runtime memory constraints
- Payload size restrictions
- Execution timeouts

## Project Structure

```
.
├── 1_export_to_onnx.py          # Convert TensorFlow model to ONNX
├── 2_slice_model.py             # Decompose ONNX model into slices
├── 3_validate_slices.py         # Validate slices against constraints
├── handler.py                   # AWS Lambda function handler
├── create_input_and_upload.py  # Prepare and upload test input
├── deploy_lambda.py             # Deploy Lambda function
├── upload_slices_to_s3.py       # Upload slices to S3
├── deploy_step_functions.py     # Deploy Step Functions workflow
├── run_full_pipeline.py         # Complete automation script
├── test_local.py                # Local testing utilities
├── step_functions_definition.json  # Step Functions state machine (JSON)
├── step_functions_definition.yaml # Step Functions state machine (YAML)
└── README.md                    # This file
```

## Prerequisites

1. **Python 3.10+**
2. **AWS Account** with appropriate permissions
3. **AWS CLI** configured with credentials
4. **Required Python packages:**
   ```bash
   pip install tensorflow tf2onnx onnx onnxruntime numpy boto3
   ```

## Quick Start

### 1. Export Model to ONNX

```bash
python 1_export_to_onnx.py
```

This creates `mobilenetv3.onnx` from a pre-trained MobileNetV3 model.

### 2. Slice the Model

```bash
python 2_slice_model.py
```

This decomposes the ONNX model into 5 slices (configurable) in the `slices/` directory.

### 3. Validate Slices

```bash
python 3_validate_slices.py
```

Checks if slices meet Serverless platform constraints:
- File size limits
- Memory requirements
- Payload sizes (must use S3 for intermediate data)

### 4. Prepare Input Data

```bash
python create_input_and_upload.py
```

Creates a preprocessed input image and uploads it to S3.

### 5. Upload Slices to S3

```bash
python upload_slices_to_s3.py
```

Uploads all model slices to your S3 bucket.

### 6. Deploy Lambda Function

```bash
python deploy_lambda.py
```

Packages and deploys the Lambda function with required dependencies.

### 7. Deploy Step Functions Workflow

```bash
python deploy_step_functions.py
```

Creates the Step Functions state machine that orchestrates slice execution.

## Automated Pipeline

Run the complete pipeline:

```bash
python run_full_pipeline.py
```

This script guides you through all steps interactively.

## Architecture

```
┌─────────────┐
│   Input     │
│  (S3)       │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   AWS Step Functions Workflow      │
│                                     │
│  Init → ExecuteSlice → Check       │
│         (Loop)         → Done       │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   AWS Lambda Function               │
│   (handler.py)                      │
│                                     │
│  1. Download slice from S3          │
│  2. Load input from S3              │
│  3. Run ONNX inference              │
│  4. Upload output to S3             │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Output     │
│  (S3)       │
└─────────────┘
```

## Step Functions Workflow

The workflow consists of 4 states:

1. **Init**: Initialize workflow parameters
2. **ExecuteSlice**: Invoke Lambda function for current slice
3. **IsExecutionCompleted**: Check if all slices are done
4. **Done**: Return final result

The workflow loops through ExecuteSlice until all slices are processed.

## Lambda Function Handler

The `handler.py` implements:
- S3 download/upload for models and data
- ONNX Runtime inference
- Session caching for warm starts
- Error handling and logging
- Proper tensor name matching

## Configuration

Key parameters you may need to adjust:

- **Number of slices**: Edit `num_slices` in `2_slice_model.py`
- **S3 bucket name**: Update `BUCKET_NAME` in upload/deploy scripts
- **Lambda memory**: Adjust `LAMBDA_MEMORY` in `deploy_lambda.py`
- **Model prefix**: Change S3 key prefixes as needed

## Testing

### Local Testing

```bash
python test_local.py
```

Note: Full local testing requires S3 access or LocalStack for local S3 simulation.

### Manual Testing

1. Test ONNX export and slicing locally
2. Validate slices meet constraints
3. Test Lambda function with test events
4. Execute Step Functions workflow with sample input

## Monitoring

- **CloudWatch Logs**: Lambda function logs
- **Step Functions Console**: Visual workflow execution
- **CloudWatch Metrics**: Execution time, memory usage, errors

## Cost Considerations

- Lambda: Pay per invocation and memory allocation
- Step Functions: Pay per state transition
- S3: Storage and request costs
- Data transfer: Between Lambda and S3

Optimize by:
- Choosing appropriate number of slices (balance memory vs. latency)
- Using appropriate Lambda memory settings
- Minimizing S3 requests (caching, batch operations)

## Limitations & Future Work

Current implementation:
- ✅ Model decomposition
- ✅ Sequential slice execution
- ✅ S3-based intermediate storage
- ✅ Error handling and retries

Potential improvements:
- Parallel slice execution (for models with branching)
- Dynamic slice sizing based on constraints
- Support for more model architectures
- Multi-cloud deployment (Azure, GCP)

## Research Paper

This implementation is based on:
> Gallego, A., et al. (2023). "Machine Learning Inference on Serverless Platforms Using Model Decomposition." UCC '23.

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]



