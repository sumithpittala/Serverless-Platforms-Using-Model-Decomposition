import tensorflow as tf
import tf2onnx

model = tf.keras.applications.MobileNetV3Small(
    input_shape=(224, 224, 3),
    include_top=True,
    weights="imagenet"   
)

spec = (tf.TensorSpec((1, 224, 224, 3), tf.float32, name="input"),)
output_path = "mobilenetv3.onnx"

model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec)

with open(output_path, "wb") as f:
    f.write(model_proto.SerializeToString())

print("✔ MobileNetV3 downloaded and exported to mobilenetv3.onnx")
