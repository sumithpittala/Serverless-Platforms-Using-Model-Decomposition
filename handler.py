import boto3
import numpy as np
import onnx
import onnxruntime as ort
import io
import os
import json
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")


def load_numpy_from_s3(bucket, key):
    # Use download_fileobj to avoid saving to disk unnecessarily
    buf = io.BytesIO()
    s3.download_fileobj(bucket, key, buf)
    buf.seek(0)
    return np.load(buf)


def lambda_handler(event, context):
    try:
        bucket = event["bucket"]
        slice_id = int(event["slice_id"])
        total_slices = int(event["total_slices"])

        input_key = event["input_key"]
        output_key = event["output_key"]
    except Exception as e:
        logger.exception("Invalid event payload: %s", e)
        raise

    model_key = f"mobilenetv3/slices/slice_{slice_id}.onnx"

    try:
        # download model to /tmp for onnxruntime
        s3.download_file(bucket, model_key, "/tmp/model.onnx")

        # inspect model to determine which graph inputs are initializers
        onnx_model = onnx.load("/tmp/model.onnx")
        initializer_names = {init.name for init in onnx_model.graph.initializer}

        session = ort.InferenceSession("/tmp/model.onnx")

        # Build feed dict: support either a single 'input_key' (for single-input slices)
        # or an 'input_keys' mapping from tensor-name -> s3 key for multi-input slices.
        feed = {}
        declared_inputs = [inp.name for inp in onnx_model.graph.input]
        non_init_inputs = [n for n in declared_inputs if n not in initializer_names]

        # If user provided explicit mapping, use it
        input_keys_map = event.get("input_keys")
        if input_keys_map and isinstance(input_keys_map, dict):
            for tensor_name in non_init_inputs:
                key = input_keys_map.get(tensor_name)
                if key is None:
                    raise ValueError(f"Missing input key for tensor: {tensor_name}")
                feed[tensor_name] = load_numpy_from_s3(bucket, key)
        else:
            # fallback to single input_key: only valid when there is exactly one non-init input
            if len(non_init_inputs) == 1:
                if not input_key:
                    raise ValueError("Missing 'input_key' for single-input slice")
                feed[non_init_inputs[0]] = load_numpy_from_s3(bucket, input_key)
            else:
                raise ValueError("This slice expects multiple inputs; provide 'input_keys' mapping in the event")

        # ONNX Runtime expects a dict keyed by session input names; ensure we map correctly
        # session.get_inputs() returns InputMeta objects with .name matching model input names
        runtime_feed = {}
        for inp in session.get_inputs():
            name = inp.name
            if name in feed:
                runtime_feed[name] = feed[name]

        outputs = session.run(None, runtime_feed)

        # save output to buffer and upload
        out_buf = io.BytesIO()
        np.save(out_buf, outputs[0])
        out_buf.seek(0)

        s3.upload_fileobj(out_buf, bucket, output_key)

        result = {
            "next_slice": slice_id + 1,
            "continue": slice_id + 1 < total_slices,
            "input_key_next": output_key
        }
        logger.info("Slice %s executed, uploaded to %s", slice_id, output_key)
        return result
    except Exception:
        logger.exception("Error running slice %s", slice_id)
        raise
