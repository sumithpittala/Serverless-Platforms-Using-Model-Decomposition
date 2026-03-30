"""
Robust ONNX graph slicer

Creates N contiguous node-range slices from an ONNX model while preserving
correct explicit graph inputs, outputs, and initializers for each slice.

Usage:
  python 2_slice_model.py --model mobilenetv3.onnx --slices 5 --out_dir slices

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
        g_inputs = []
        for name in slice_inputs:
            if name in vi_map:
                g_inputs.append(vi_map[name])
            elif name in required_inits:
                init = required_inits[name]
                g_inputs.append(helper.make_tensor_value_info(name, init.data_type, list(init.dims)))
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
"""
Robust ONNX graph slicer

Creates N contiguous node-range slices from an ONNX model while preserving
correct explicit graph inputs, outputs, and initializers for each slice.

Usage:
  python 2_slice_model.py --model mobilenetv3.onnx --slices 5 --out_dir slices

Each produced slice is validated with `onnx.checker.check_model` and saved
as `slice_{i}.onnx` in the output directory.
"""
import argparse
import math
import os
import onnx
from onnx import helper, checker, numpy_helper


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

        # Collect initializers required by the slice (those referenced by its nodes)
        required_inits = {}
        for n in slice_nodes:
            for inp in n.input:
                if inp in init_map:
                    required_inits[inp] = init_map[inp]

        # Build graph inputs ValueInfoProto for slice_inputs
        g_inputs = []
        for name in slice_inputs:
            if name in vi_map:
                g_inputs.append(vi_map[name])
            elif name in required_inits:
                init = required_inits[name]
                g_inputs.append(helper.make_tensor_value_info(name, init.data_type, list(init.dims)))
            else:
                # If we have no info, try to fall back to a generic (unknown) tensor
                # Creating an empty ValueInfoProto is acceptable for many runtimes
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
import onnx
from onnx import helper, shape_inference
import os

model_path = "mobilenetv3.onnx"
output_folder = "slices"
num_slices = 5

os.makedirs(output_folder, exist_ok=True)

model = onnx.load(model_path)
layers = model.graph.node
total_layers = len(layers)
split_size = total_layers // num_slices

for i in range(num_slices):
    start = i * split_size
    end = (i + 1) * split_size if i < num_slices - 1 else total_layers

    slice_layers = layers[start:end]

    graph = helper.make_graph(
        slice_layers,
        f"slice_{i}",
        model.graph.input,
        model.graph.output
    )

    slice_model = helper.make_model(graph)
    slice_model = shape_inference.infer_shapes(slice_model)

    save_path = f"{output_folder}/slice_{i}.onnx"
    onnx.save(slice_model, save_path)

    print("Created:", save_path)

print("Slices ready")
import onnx
from onnx import helper, shape_inference
from collections import defaultdict
import os

model_path = "mobilenetv3.onnx"
output_folder = "slices"
num_slices = 5

os.makedirs(output_folder, exist_ok=True)

model = onnx.load(model_path)
nodes = list(model.graph.node)
total_nodes = len(nodes)
split_size = total_nodes // num_slices

# Build producer/consumer maps
producer = {}  # tensor_name -> node_index
consumers = defaultdict(list)  # tensor_name -> list of node_index
for idx, node in enumerate(nodes):
    for out in node.output:
        producer[out] = idx
    for inp in node.input:
        consumers[inp].append(idx)

# Value info and initializers lookup
value_info_map = {vi.name: vi for vi in list(model.graph.value_info) + list(model.graph.input) + list(model.graph.output)}
initializer_map = {init.name: init for init in model.graph.initializer}

def get_value_info(name):
    if name in value_info_map:
        return value_info_map[name]
    # fallback generic
    return helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None)

print(f"Total nodes: {total_nodes}")
print(f"Creating {num_slices} slices...")

for i in range(num_slices):
    start = i * split_size
    end = (i + 1) * split_size if i < num_slices - 1 else total_nodes
    slice_nodes = nodes[start:end]

    # tensors produced and consumed inside this slice
    produced = set(o for n in slice_nodes for o in n.output)
    consumed = set(inp for n in slice_nodes for inp in n.input)

    # inputs are consumed tensors not produced in this slice
    slice_input_names = sorted([name for name in consumed if name not in produced])

    # outputs are produced tensors consumed outside this slice or model outputs
    slice_output_names = []
    model_output_names = {o.name for o in model.graph.output}
    for name in produced:
        outside = [c for c in consumers.get(name, []) if c < start or c >= end]
        if outside or name in model_output_names:
            slice_output_names.append(name)

    if not slice_output_names:
        import onnx
        from onnx import helper, shape_inference
        from collections import defaultdict
        import os

        model_path = "mobilenetv3.onnx"
        output_folder = "slices"
        num_slices = 5

        os.makedirs(output_folder, exist_ok=True)

        model = onnx.load(model_path)
        nodes = list(model.graph.node)
        total_nodes = len(nodes)
        split_size = total_nodes // num_slices

        # Build producer/consumer maps
        producer = {}  # tensor_name -> node_index
        consumers = defaultdict(list)  # tensor_name -> list of node_index
        for idx, node in enumerate(nodes):
            for out in node.output:
                producer[out] = idx
            for inp in node.input:
                consumers[inp].append(idx)

        # Value info and initializers lookup
        value_info_map = {vi.name: vi for vi in list(model.graph.value_info) + list(model.graph.input) + list(model.graph.output)}
        initializer_map = {init.name: init for init in model.graph.initializer}

        def get_value_info(name):
            if name in value_info_map:
                return value_info_map[name]
            # fallback generic
            return helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None)

        print(f"Total nodes: {total_nodes}")
        print(f"Creating {num_slices} slices...")

        for i in range(num_slices):
            start = i * split_size
            end = (i + 1) * split_size if i < num_slices - 1 else total_nodes
            slice_nodes = nodes[start:end]

            # tensors produced and consumed inside this slice
            produced = set(o for n in slice_nodes for o in n.output)
            consumed = set(inp for n in slice_nodes for inp in n.input)

            # inputs are consumed tensors not produced in this slice
            slice_input_names = sorted([name for name in consumed if name not in produced])

            # outputs are produced tensors consumed outside this slice or model outputs
            slice_output_names = []
            model_output_names = {o.name for o in model.graph.output}
            for name in produced:
                outside = [c for c in consumers.get(name, []) if c < start or c >= end]
                if outside or name in model_output_names:
                    slice_output_names.append(name)

            if not slice_output_names:
                # fallback: expose all produced tensors
                slice_output_names = list(produced)

            # build ValueInfoProto lists
            input_vis = []
            for name in slice_input_names:
                if name in initializer_map:
                    # initializers are inputs too
                    input_vis.append(helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None))
                else:
                    input_vis.append(get_value_info(name))

            output_vis = [get_value_info(name) for name in slice_output_names]

            # collect relevant initializers
            slice_initializers = [init for init in model.graph.initializer if init.name in produced or init.name in slice_input_names]

            graph = helper.make_graph(
                list(slice_nodes),
                f"slice_{i}",
                inputs=input_vis,
                outputs=output_vis,
                initializer=slice_initializers
            )

            slice_model = helper.make_model(graph)
            try:
                slice_model = shape_inference.infer_shapes(slice_model)
            except Exception:
                pass

            save_path = os.path.join(output_folder, f"slice_{i}.onnx")
            onnx.save(slice_model, save_path)
            print(f"Created: {save_path} (inputs: {len(input_vis)}, outputs: {len(output_vis)})")

        print("Slices ready")
                import onnx
