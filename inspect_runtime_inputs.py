import onnx
import onnxruntime as ort
from pathlib import Path
p=Path('slices')
for f in sorted(p.glob('slice_*.onnx')):
    print('\n', f.name)
    m=onnx.load(str(f))
    print(' graph.inputs:', [i.name for i in m.graph.input])
    print(' graph.initializers_count:', len(m.graph.initializer))
    sess=ort.InferenceSession(str(f))
    print(' session.inputs:', [i.name for i in sess.get_inputs()])
    print(' session.outputs:', [o.name for o in sess.get_outputs()])
