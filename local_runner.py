<<<<<<< HEAD
<<<<<<< HEAD
"""Local runner to sequentially execute ONNX slices and measure timings.

This simulates the serverless workflow locally without S3 or Step Functions.

Usage:
  python local_runner.py --slices slices --input input.npy --out-dir local_outputs
"""

import time
import argparse
from pathlib import Path
import numpy as np
import io
import onnx
import onnxruntime as ort


def run_slices(slices_folder: Path, input_path: Path, out_dir: Path):
    slice_files = sorted(slices_folder.glob('slice_*.onnx'))
    if not slice_files:
        raise SystemExit('No slice_*.onnx files found in ' + str(slices_folder))

    data = np.load(str(input_path))
    out_dir.mkdir(parents=True, exist_ok=True)

    report = []
    previous_outputs_map = None

    for i, sf in enumerate(slice_files):
        # inspect slice declared inputs/initializers so we feed only non-initializer inputs
        m = onnx.load(str(sf))
        declared_inputs = [inp.name for inp in m.graph.input]
        initializer_names = {init.name for init in m.graph.initializer}
        non_init_inputs = [n for n in declared_inputs if n not in initializer_names]

        # choose which tensor name to feed for this slice
        if previous_outputs_map is None:
            # first slice: prefer declared non-init input or fall back to first declared input
            if non_init_inputs:
                feed_name = non_init_inputs[0]
            elif declared_inputs:
                feed_name = declared_inputs[0]
            else:
                raise RuntimeError(f'No inputs found for slice {sf.name}')
            feed_array = data
        else:
            # build feed dict from previous outputs for all inputs this slice expects
            feed_dict = {}
            for cand in non_init_inputs:
                if cand in previous_outputs_map:
                    feed_dict[cand] = previous_outputs_map[cand]

            if not feed_dict:
                # no name matches; if previous slice produced exactly one tensor, use it
                if len(previous_outputs_map) == 1 and non_init_inputs:
                    feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                else:
                    # fall back: use first available previous output for first non-init input
                    if non_init_inputs:
                        feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                    else:
                        raise RuntimeError(f'Cannot determine input to feed for slice {sf.name}')

        sess = ort.InferenceSession(str(sf))

        # prepare feed mapping for this run
        if previous_outputs_map is None:
            feed = {feed_name: feed_array}
        else:
            feed = feed_dict

        t0 = time.time()
        outputs = sess.run(None, feed)
        elapsed = time.time() - t0

        # Map outputs by name so we can select the matching tensor for next slice
        out_names = [o.name for o in sess.get_outputs()]
        outputs_map = {name: arr for name, arr in zip(out_names, outputs)}

        # choose a primary output array to save/measure (prefer first output)
        if outputs:
            out_arr = outputs[0]
        else:
            out_arr = np.array([])

        # measure serialized size
        buf = io.BytesIO()
        np.save(buf, out_arr)
        size = len(buf.getvalue())

        out_path = out_dir / f'intermediate_{i}.npy'
        np.save(str(out_path), out_arr)

        report.append({'slice': i, 'file': str(sf.name), 'time_s': elapsed, 'bytes': size, 'output_path': str(out_path), 'fed_input': list(feed.keys())})

        # prepare for next iteration
        previous_outputs_map = outputs_map
        data = out_arr

    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--slices', type=str, default='slices', help='Folder with slice_*.onnx')
    p.add_argument('--input', type=str, default='input.npy', help='Input numpy file')
    p.add_argument('--out-dir', type=str, default='local_outputs', help='Folder to store intermediate outputs')
    args = p.parse_args()

    slices_folder = Path(args.slices)
    input_path = Path(args.input)
    out_dir = Path(args.out_dir)

    if not input_path.exists():
        raise SystemExit(f'Input file not found: {input_path}')

    report = run_slices(slices_folder, input_path, out_dir)

    print('\nRun summary:')
    total_time = 0.0
    total_bytes = 0
    for r in report:
        print(f"Slice {r['slice']:>2}: {r['file']:<20} time={r['time_s']:.4f}s size={r['bytes']} bytes -> {r['output_path']}")
        total_time += r['time_s']
        total_bytes += r['bytes']

    print(f"\nTotal slices: {len(report)}, total_time={total_time:.4f}s, final_payload={total_bytes} bytes")


if __name__ == '__main__':
    main()
=======
"""Local runner to sequentially execute ONNX slices and measure timings.

This simulates the serverless workflow locally without S3 or Step Functions.

Usage:
  python local_runner.py --slices slices --input input.npy --out-dir local_outputs
"""

import time
import argparse
from pathlib import Path
import numpy as np
import io
import onnx
import onnxruntime as ort


def run_slices(slices_folder: Path, input_path: Path, out_dir: Path):
    slice_files = sorted(slices_folder.glob('slice_*.onnx'))
    if not slice_files:
        raise SystemExit('No slice_*.onnx files found in ' + str(slices_folder))

    data = np.load(str(input_path))
    out_dir.mkdir(parents=True, exist_ok=True)

    report = []
    previous_outputs_map = None

    for i, sf in enumerate(slice_files):
        # inspect slice declared inputs/initializers so we feed only non-initializer inputs
        m = onnx.load(str(sf))
        declared_inputs = [inp.name for inp in m.graph.input]
        initializer_names = {init.name for init in m.graph.initializer}
        non_init_inputs = [n for n in declared_inputs if n not in initializer_names]

        # choose which tensor name to feed for this slice
        if previous_outputs_map is None:
            # first slice: prefer declared non-init input or fall back to first declared input
            if non_init_inputs:
                feed_name = non_init_inputs[0]
            elif declared_inputs:
                feed_name = declared_inputs[0]
            else:
                raise RuntimeError(f'No inputs found for slice {sf.name}')
            feed_array = data
        else:
            # build feed dict from previous outputs for all inputs this slice expects
            feed_dict = {}
            for cand in non_init_inputs:
                if cand in previous_outputs_map:
                    feed_dict[cand] = previous_outputs_map[cand]

            if not feed_dict:
                # no name matches; if previous slice produced exactly one tensor, use it
                if len(previous_outputs_map) == 1 and non_init_inputs:
                    feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                else:
                    # fall back: use first available previous output for first non-init input
                    if non_init_inputs:
                        feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                    else:
                        raise RuntimeError(f'Cannot determine input to feed for slice {sf.name}')

        sess = ort.InferenceSession(str(sf))

        # prepare feed mapping for this run
        if previous_outputs_map is None:
            feed = {feed_name: feed_array}
        else:
            feed = feed_dict

        t0 = time.time()
        outputs = sess.run(None, feed)
        elapsed = time.time() - t0

        # Map outputs by name so we can select the matching tensor for next slice
        out_names = [o.name for o in sess.get_outputs()]
        outputs_map = {name: arr for name, arr in zip(out_names, outputs)}

        # choose a primary output array to save/measure (prefer first output)
        if outputs:
            out_arr = outputs[0]
        else:
            out_arr = np.array([])

        # measure serialized size
        buf = io.BytesIO()
        np.save(buf, out_arr)
        size = len(buf.getvalue())

        out_path = out_dir / f'intermediate_{i}.npy'
        np.save(str(out_path), out_arr)

        report.append({'slice': i, 'file': str(sf.name), 'time_s': elapsed, 'bytes': size, 'output_path': str(out_path), 'fed_input': list(feed.keys())})

        # prepare for next iteration
        previous_outputs_map = outputs_map
        data = out_arr

    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--slices', type=str, default='slices', help='Folder with slice_*.onnx')
    p.add_argument('--input', type=str, default='input.npy', help='Input numpy file')
    p.add_argument('--out-dir', type=str, default='local_outputs', help='Folder to store intermediate outputs')
    args = p.parse_args()

    slices_folder = Path(args.slices)
    input_path = Path(args.input)
    out_dir = Path(args.out_dir)

    if not input_path.exists():
        raise SystemExit(f'Input file not found: {input_path}')

    report = run_slices(slices_folder, input_path, out_dir)

    print('\nRun summary:')
    total_time = 0.0
    total_bytes = 0
    for r in report:
        print(f"Slice {r['slice']:>2}: {r['file']:<20} time={r['time_s']:.4f}s size={r['bytes']} bytes -> {r['output_path']}")
        total_time += r['time_s']
        total_bytes += r['bytes']

    print(f"\nTotal slices: {len(report)}, total_time={total_time:.4f}s, final_payload={total_bytes} bytes")


if __name__ == '__main__':
    main()
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
=======
"""Local runner to sequentially execute ONNX slices and measure timings.

This simulates the serverless workflow locally without S3 or Step Functions.

Usage:
  python local_runner.py --slices slices --input input.npy --out-dir local_outputs
"""

import time
import argparse
from pathlib import Path
import numpy as np
import io
import onnx
import onnxruntime as ort


def run_slices(slices_folder: Path, input_path: Path, out_dir: Path):
    slice_files = sorted(slices_folder.glob('slice_*.onnx'))
    if not slice_files:
        raise SystemExit('No slice_*.onnx files found in ' + str(slices_folder))

    data = np.load(str(input_path))
    out_dir.mkdir(parents=True, exist_ok=True)

    report = []
    previous_outputs_map = None

    for i, sf in enumerate(slice_files):
        # inspect slice declared inputs/initializers so we feed only non-initializer inputs
        m = onnx.load(str(sf))
        declared_inputs = [inp.name for inp in m.graph.input]
        initializer_names = {init.name for init in m.graph.initializer}
        non_init_inputs = [n for n in declared_inputs if n not in initializer_names]

        # choose which tensor name to feed for this slice
        if previous_outputs_map is None:
            # first slice: prefer declared non-init input or fall back to first declared input
            if non_init_inputs:
                feed_name = non_init_inputs[0]
            elif declared_inputs:
                feed_name = declared_inputs[0]
            else:
                raise RuntimeError(f'No inputs found for slice {sf.name}')
            feed_array = data
        else:
            # build feed dict from previous outputs for all inputs this slice expects
            feed_dict = {}
            for cand in non_init_inputs:
                if cand in previous_outputs_map:
                    feed_dict[cand] = previous_outputs_map[cand]

            if not feed_dict:
                # no name matches; if previous slice produced exactly one tensor, use it
                if len(previous_outputs_map) == 1 and non_init_inputs:
                    feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                else:
                    # fall back: use first available previous output for first non-init input
                    if non_init_inputs:
                        feed_dict[non_init_inputs[0]] = next(iter(previous_outputs_map.values()))
                    else:
                        raise RuntimeError(f'Cannot determine input to feed for slice {sf.name}')

        sess = ort.InferenceSession(str(sf))

        # prepare feed mapping for this run
        if previous_outputs_map is None:
            feed = {feed_name: feed_array}
        else:
            feed = feed_dict

        t0 = time.time()
        outputs = sess.run(None, feed)
        elapsed = time.time() - t0

        # Map outputs by name so we can select the matching tensor for next slice
        out_names = [o.name for o in sess.get_outputs()]
        outputs_map = {name: arr for name, arr in zip(out_names, outputs)}

        # choose a primary output array to save/measure (prefer first output)
        if outputs:
            out_arr = outputs[0]
        else:
            out_arr = np.array([])

        # measure serialized size
        buf = io.BytesIO()
        np.save(buf, out_arr)
        size = len(buf.getvalue())

        out_path = out_dir / f'intermediate_{i}.npy'
        np.save(str(out_path), out_arr)

        report.append({'slice': i, 'file': str(sf.name), 'time_s': elapsed, 'bytes': size, 'output_path': str(out_path), 'fed_input': list(feed.keys())})

        # prepare for next iteration
        previous_outputs_map = outputs_map
        data = out_arr

    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--slices', type=str, default='slices', help='Folder with slice_*.onnx')
    p.add_argument('--input', type=str, default='input.npy', help='Input numpy file')
    p.add_argument('--out-dir', type=str, default='local_outputs', help='Folder to store intermediate outputs')
    args = p.parse_args()

    slices_folder = Path(args.slices)
    input_path = Path(args.input)
    out_dir = Path(args.out_dir)

    if not input_path.exists():
        raise SystemExit(f'Input file not found: {input_path}')

    report = run_slices(slices_folder, input_path, out_dir)

    print('\nRun summary:')
    total_time = 0.0
    total_bytes = 0
    for r in report:
        print(f"Slice {r['slice']:>2}: {r['file']:<20} time={r['time_s']:.4f}s size={r['bytes']} bytes -> {r['output_path']}")
        total_time += r['time_s']
        total_bytes += r['bytes']

    print(f"\nTotal slices: {len(report)}, total_time={total_time:.4f}s, final_payload={total_bytes} bytes")


if __name__ == '__main__':
    main()
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
