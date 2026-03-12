import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "my_cnn_model.keras"
DATASET_DIR = BASE_DIR / "Metal oxides"
CLASS_NAMES_PATH = BASE_DIR / "class_names.json"
IMG_HEIGHT = 150
IMG_WIDTH = 150


def _read_class_names(dataset_dir: Path) -> list[str]:
    if not dataset_dir.exists():
        return []
    return sorted([item.name for item in dataset_dir.iterdir() if item.is_dir()])


def _read_class_names_json(json_path: Path) -> list[str]:
    if not json_path.exists():
        return []
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, list):
        return [str(name) for name in data]
    return []


CLASS_NAMES = _read_class_names_json(CLASS_NAMES_PATH) or _read_class_names(DATASET_DIR)
MODEL = None

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")


def get_model() -> tf.keras.Model:
    global MODEL
    if MODEL is None:
        MODEL = tf.keras.models.load_model(MODEL_PATH)
    return MODEL


def predict_from_bytes(image_bytes: bytes) -> dict:
    image = tf.image.decode_image(image_bytes, channels=3, expand_animations=False)
    image = tf.image.resize(image, [IMG_HEIGHT, IMG_WIDTH])
    image = tf.cast(image, tf.float32)
    image = tf.expand_dims(image, axis=0)

    model = get_model()
    raw_output = np.asarray(model.predict(image, verbose=0)[0], dtype=np.float32)
    if np.all(raw_output >= 0.0) and np.isclose(float(np.sum(raw_output)), 1.0, atol=1e-3):
        probabilities = raw_output
    else:
        probabilities = tf.nn.softmax(raw_output).numpy()

    predicted_index = int(np.argmax(probabilities))
    predicted_class = (
        CLASS_NAMES[predicted_index]
        if predicted_index < len(CLASS_NAMES)
        else f"class_{predicted_index}"
    )

    top_indices = np.argsort(probabilities)[::-1][:3]
    top_predictions = []
    for idx in top_indices:
        class_name = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else f"class_{idx}"
        top_predictions.append(
            {
                "class_name": class_name,
                "confidence": float(probabilities[idx]),
            }
        )

    return {
        "predicted_class": predicted_class,
        "confidence": float(probabilities[predicted_index]),
        "top_predictions": top_predictions,
    }


@app.route("/")
def serve_index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/predict", methods=["POST"])
def predict_image():
    if "image" not in request.files:
        return jsonify({"error": "Missing image file. Use field name 'image'."}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    if not image_bytes:
        return jsonify({"error": "Empty image file."}), 400

    try:
        result = predict_from_bytes(image_bytes)
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        return jsonify({"error": f"Prediction failed: {exc}"}), 500

    return jsonify(result)


@app.route("/<path:path>")
def serve_static(path: str):
    target = BASE_DIR / path
    if target.exists() and target.is_file():
        return send_from_directory(BASE_DIR, path)
    return send_from_directory(BASE_DIR, "index.html")


if __name__ == "__main__":
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    get_model()
    app.run(host="127.0.0.1", port=5000, debug=True)
