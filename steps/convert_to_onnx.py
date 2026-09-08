"""Step 4 — Convert the freshly retrained scikit-learn model to ONNX.

ONNX is the hand-off point between the "training side" (ZenML + scikit-learn,
can be a heavier Python environment) and the "serving side" (a tiny Docker
container that only needs onnxruntime). The two never need the same
dependencies, which is what keeps the edge container small enough to run on
low-spec factory-floor hardware.
"""
import onnx.helper
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from zenml import step


@step(enable_cache=False)
def convert_to_onnx(model: object, metrics: dict, cfg: dict) -> bytes:
    if metrics.get("skipped"):
        return b""  # nothing to convert; deploy_to_edge will no-op too

    n_features = len(metrics["features"])
    initial_type = [("input", FloatTensorType([None, n_features]))]
    original_make_attribute = onnx.helper.make_attribute

    def make_attribute_with_integer_bools(name, value, *args, **kwargs):
        if isinstance(value, (list, tuple)):
            value = [int(item) if isinstance(item, bool) else item for item in value]
        return original_make_attribute(name, value, *args, **kwargs)

    onnx.helper.make_attribute = make_attribute_with_integer_bools
    try:
        onnx_model = convert_sklearn(
            model,
            initial_types=initial_type,
            target_opset={"": 17, "ai.onnx.ml": 3},
        )
    finally:
        onnx.helper.make_attribute = original_make_attribute
    return onnx_model.SerializeToString()
