<<<<<<< HEAD
import onnx
from pathlib import Path
p = Path('slices')
files = sorted(p.glob('slice_*.onnx'))
if not files:
    print('No slices found in slices/')
for f in files:
    m = onnx.load(str(f))
    inputs = [i.name for i in m.graph.input]
    outputs = [o.name for o in m.graph.output]
    initials = [init.name for init in m.graph.initializer]
    print(f.name)
    print('  inputs:', inputs)
    print('  outputs:', outputs)
    print('  initializers_count:', len(initials))
=======
import onnx
from pathlib import Path
p = Path('slices')
files = sorted(p.glob('slice_*.onnx'))
if not files:
    print('No slices found in slices/')
for f in files:
    m = onnx.load(str(f))
    inputs = [i.name for i in m.graph.input]
    outputs = [o.name for o in m.graph.output]
    initials = [init.name for init in m.graph.initializer]
    print(f.name)
    print('  inputs:', inputs)
    print('  outputs:', outputs)
    print('  initializers_count:', len(initials))
>>>>>>> 18d4c84070273e123ca5c9919152b87f699818ab
