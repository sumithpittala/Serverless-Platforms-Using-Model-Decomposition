"""
Robust ONNX graph slicer (clean copy)

Creates N contiguous node-range slices from an ONNX model while preserving
correct explicit graph inputs, outputs, and initializers for each slice.

Usage:
  python 2_slice_model_clean.py --model mobilenetv3.onnx --slices 5 --out_dir slices

Each produced slice is validated with `onnx.checker.check_model` and saved
as `slice_{i}.onnx` in the output directory.
"""
import argparse
import math
import os
import onnx
from onnx import helper, checker


def build_value_info_map(model):
    """Return a map name -> ValueInfoProto using inferred shapes when possible."""
    try:
        inferred = onnx.shape_inference.infer_shapes(model)
    except Exception:
        inferred = model

    vi_map = {}
    for vi in list(inferred.graph.input) + list(inferred.graph.value_info) + list(inferred.graph.output):
        vi_map[vi.name] = vi
    return vi_map


def get_initializer_map(model):
    return {init.name: init for init in model.graph.initializer}


def partition_indices(total, n_parts):
    per = math.ceil(total / float(n_parts))
    parts = []
    for i in range(n_parts):
        start = i * per
        end = min((i + 1) * per, total)
        if start >= end:
            break
        parts.append((start, end))
    return parts


def slice_model(model_path, n_slices=2, out_dir="slices"):
    model = onnx.load(model_path)
    vi_map = build_value_info_map(model)
    init_map = get_initializer_map(model)

    nodes = list(model.graph.node)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    parts = partition_indices(len(nodes), n_slices)
    model_outputs = {o.name for o in model.graph.output}

    for idx, (start, end) in enumerate(parts):
        slice_nodes = nodes[start:end]

        produced = set()
        consumed = set()
        for n in slice_nodes:
            for o in n.output:
                produced.add(o)
            for i in n.input:
                consumed.add(i)

        # Inputs to the slice are consumed names that are not produced inside the slice
        slice_inputs = [name for name in consumed if name not in produced]

        # Outputs are produced names that are consumed outside the slice or are model outputs
        produced_consumed_elsewhere = set()
        for i_node, n in enumerate(nodes):
            if i_node >= start and i_node < end:
                continue
            # other nodes consume these names
            for i in n.input:
                if i in produced:
                    produced_consumed_elsewhere.add(i)

        slice_outputs = [name for name in produced if (name in produced_consumed_elsewhere or name in model_outputs)]

        # fallback: if no outputs were discovered, expose all produced tensors
        if not slice_outputs:
            slice_outputs = list(produced)

        # Collect initializers required by the slice (those referenced by its nodes)
        required_inits = {}
        for n in slice_nodes:
            for inp in n.input:
                if inp in init_map:
                    required_inits[inp] = init_map[inp]

        # Build graph inputs ValueInfoProto for slice_inputs
        # If a slice input is an initializer (constant/weight), do NOT add it to
        # graph.inputs — keep it only in `initializer`. Many exporters include
        # constants as graph inputs which forces runtimes to expect them as feed.
        g_inputs = []
        for name in slice_inputs:
            if name in required_inits:
                # initializer only; skip adding to graph inputs
                continue
            if name in vi_map:
                g_inputs.append(vi_map[name])
            else:
                # If we have no info, create an empty value info (some runtimes accept this)
                g_inputs.append(helper.make_empty_tensor_value_info(name))

        # Build graph outputs ValueInfoProto for slice_outputs
        g_outputs = []
        for name in slice_outputs:
            if name in vi_map:
                g_outputs.append(vi_map[name])
            elif name in required_inits:
                init = required_inits[name]
                g_outputs.append(helper.make_tensor_value_info(name, init.data_type, list(init.dims)))
            else:
                g_outputs.append(helper.make_empty_tensor_value_info(name))

        # Compose new graph
        new_graph = helper.make_graph(
            nodes=[n for n in slice_nodes],
            name=f"slice_{idx}",
            inputs=g_inputs,
            outputs=g_outputs,
            initializer=list(required_inits.values()),
        )

        new_model = helper.make_model(new_graph, opset_imports=model.opset_import)

        # Copy metadata from original model when possible
        if model.ir_version:
            new_model.ir_version = model.ir_version

        out_path = os.path.join(out_dir, f"slice_{idx}.onnx")
        onnx.save(new_model, out_path)

        # Validate saved model
        try:
            m = onnx.load(out_path)
            checker.check_model(m)
            print(f"Saved and validated slice: {out_path} (nodes {start}:{end})")
        except Exception as e:
            print(f"Validation failed for slice {idx} ({out_path}): {e}")


def parse_args():
    p = argparse.ArgumentParser(description="Slice an ONNX graph into N contiguous node ranges")
    p.add_argument("--model", required=True, help="Path to input ONNX model")
    p.add_argument("--slices", type=int, default=2, help="Number of slices to create")
    p.add_argument("--out_dir", default="slices", help="Output directory for slices")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    slice_model(args.model, n_slices=args.slices, out_dir=args.out_dir)
