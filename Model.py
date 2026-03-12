import json
from pathlib import Path

import numpy as np
import tensorflow as tf

layers = tf.keras.layers

# ==========================================
# 1. إعداد المسارات والمتغيرات الأساسية
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "Metal oxides"
TEST_DIR = BASE_DIR / "Metal oxides_test"

MODEL_PATH = BASE_DIR / "my_cnn_model.keras"
BEST_MODEL_PATH = BASE_DIR / "best_model.keras"
CLASS_NAMES_PATH = BASE_DIR / "class_names.json"
TEST_REPORT_JSON_PATH = BASE_DIR / "test_report.json"
TEST_REPORT_TXT_PATH = BASE_DIR / "test_report.txt"

BATCH_SIZE = 8
IMG_HEIGHT = 150
IMG_WIDTH = 150
VAL_SPLIT = 0.2
SEED = 123

HEAD_EPOCHS = 20
FINE_TUNE_EPOCHS = 12
INITIAL_LR = 1e-3
FINE_TUNE_LR = 1e-5


def build_base_model() -> tf.keras.Model:
  """Create MobileNetV2 backbone and try loading ImageNet weights."""
  try:
    model = tf.keras.applications.MobileNetV2(
      input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
      include_top=False,
      weights="imagenet",
    )
    print("تم تحميل أوزان ImageNet المسبقة بنجاح.")
  except Exception as exc:
    print(f"تعذر تحميل أوزان ImageNet: {exc}")
    print("سيتم المتابعة بأوزان عشوائية. لا يزال التدريب يعمل، لكن الدقة قد تكون أقل.")
    model = tf.keras.applications.MobileNetV2(
      input_shape=(IMG_HEIGHT, IMG_WIDTH, 3),
      include_top=False,
      weights=None,
    )
  return model


def save_class_names(names: list[str]) -> None:
  CLASS_NAMES_PATH.write_text(
    json.dumps(names, ensure_ascii=False, indent=2),
    encoding="utf-8",
  )
  print(f"تم حفظ أسماء الفئات في: {CLASS_NAMES_PATH}")


def collect_predictions(model: tf.keras.Model, dataset: tf.data.Dataset) -> tuple[np.ndarray, np.ndarray]:
  """Collect true and predicted labels from a dataset."""
  y_true: list[int] = []
  y_pred: list[int] = []

  for images, labels in dataset:
    probs = model.predict(images, verbose=0)
    preds = tf.argmax(probs, axis=1)
    y_true.extend(labels.numpy().tolist())
    y_pred.extend(preds.numpy().tolist())

  return np.asarray(y_true, dtype=np.int32), np.asarray(y_pred, dtype=np.int32)


def print_classification_report(y_true: np.ndarray, y_pred: np.ndarray, class_names: list[str]) -> dict[str, object]:
  """Print confusion matrix and return report details for saving."""
  cm = tf.math.confusion_matrix(y_true, y_pred, num_classes=len(class_names)).numpy()

  print("\nمصفوفة الالتباس (Confusion Matrix):")
  print(cm)

  report_lines = []
  per_class_rows: list[dict[str, object]] = []

  print("\nClassification Report:")
  header = f"{'Class':<12}{'Precision':>12}{'Recall':>10}{'F1-score':>10}{'Support':>10}"
  print(header)
  report_lines.append(header)

  precisions = []
  recalls = []
  f1_scores = []
  supports = []

  for i, class_name in enumerate(class_names):
    tp = float(cm[i, i])
    fp = float(cm[:, i].sum() - cm[i, i])
    fn = float(cm[i, :].sum() - cm[i, i])
    support = float(cm[i, :].sum())

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    precisions.append(precision)
    recalls.append(recall)
    f1_scores.append(f1)
    supports.append(support)

    row = f"{class_name:<12}{precision:>12.3f}{recall:>10.3f}{f1:>10.3f}{int(support):>10}"
    print(row)
    report_lines.append(row)
    per_class_rows.append(
      {
        "class_name": class_name,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "support": int(support),
      }
    )

  macro_precision = float(np.mean(precisions)) if precisions else 0.0
  macro_recall = float(np.mean(recalls)) if recalls else 0.0
  macro_f1 = float(np.mean(f1_scores)) if f1_scores else 0.0
  total_support = int(np.sum(supports)) if supports else 0

  weights = np.asarray(supports, dtype=np.float64)
  if weights.sum() > 0:
    weighted_precision = float(np.average(precisions, weights=weights))
    weighted_recall = float(np.average(recalls, weights=weights))
    weighted_f1 = float(np.average(f1_scores, weights=weights))
  else:
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0

  macro_row = f"{'macro avg':<12}{macro_precision:>12.3f}{macro_recall:>10.3f}{macro_f1:>10.3f}{total_support:>10}"
  weighted_row = f"{'weighted avg':<12}{weighted_precision:>12.3f}{weighted_recall:>10.3f}{weighted_f1:>10.3f}{total_support:>10}"
  print(macro_row)
  print(weighted_row)
  report_lines.append(macro_row)
  report_lines.append(weighted_row)

  return {
    "confusion_matrix": cm.tolist(),
    "per_class": per_class_rows,
    "macro_avg": {
      "precision": macro_precision,
      "recall": macro_recall,
      "f1_score": macro_f1,
      "support": total_support,
    },
    "weighted_avg": {
      "precision": weighted_precision,
      "recall": weighted_recall,
      "f1_score": weighted_f1,
      "support": total_support,
    },
    "text_report": "\n".join(report_lines),
  }


if __name__ == "__main__":
  if not DATASET_DIR.exists():
    raise FileNotFoundError(f"لم يتم العثور على مجلد البيانات: {DATASET_DIR}")

  tf.keras.utils.set_random_seed(SEED)

  # ==========================================
  # 2. تحميل البيانات وتقسيمها
  # ==========================================
  print("تحميل بيانات التدريب...")
  train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=VAL_SPLIT,
    subset="training",
    seed=SEED,
    image_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
  )

  print("\nتحميل بيانات التحقق...")
  val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=VAL_SPLIT,
    subset="validation",
    seed=SEED,
    image_size=(IMG_HEIGHT, IMG_WIDTH),
    batch_size=BATCH_SIZE,
  )

  class_names = train_ds.class_names
  num_classes = len(class_names)
  print(f"\nتم التعرف على الفئات التالية: {class_names}")
  save_class_names(class_names)

  # ==========================================
  # 3. تحسين خطوط البيانات والـ Augmentation
  # ==========================================
  data_augmentation = tf.keras.Sequential(
    [
      layers.RandomFlip("horizontal_and_vertical"),
      layers.RandomRotation(0.12),
      layers.RandomZoom(0.12),
      layers.RandomContrast(0.12),
    ],
    name="data_augmentation",
  )

  AUTOTUNE = tf.data.AUTOTUNE
  train_ds = train_ds.cache().shuffle(1000, seed=SEED).prefetch(buffer_size=AUTOTUNE)
  val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

  # ==========================================
  # 4. بناء نموذج Transfer Learning
  # ==========================================
  base_model = build_base_model()
  base_model.trainable = False

  inputs = tf.keras.Input(shape=(IMG_HEIGHT, IMG_WIDTH, 3))
  x = data_augmentation(inputs)
  x = layers.Rescaling(1.0 / 127.5, offset=-1.0)(x)
  x = base_model(x, training=False)
  x = layers.GlobalAveragePooling2D()(x)
  x = layers.Dropout(0.30)(x)
  outputs = layers.Dense(num_classes, activation="softmax")(x)
  model = tf.keras.Model(inputs, outputs)

  model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=INITIAL_LR),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=["accuracy"],
  )

  model.summary()

  callbacks = [
    tf.keras.callbacks.EarlyStopping(
      monitor="val_accuracy",
      patience=6,
      restore_best_weights=True,
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
      monitor="val_loss",
      factor=0.3,
      patience=3,
      min_lr=1e-6,
    ),
    tf.keras.callbacks.ModelCheckpoint(
      filepath=str(BEST_MODEL_PATH),
      monitor="val_accuracy",
      save_best_only=True,
    ),
  ]

  # ==========================================
  # 5. تدريب الرأس (Head Training)
  # ==========================================
  print("\nبدء المرحلة الأولى من التدريب...")
  model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=HEAD_EPOCHS,
    callbacks=callbacks,
  )

  # ==========================================
  # 6. Fine-Tuning لجزء من الطبقات العميقة
  # ==========================================
  print("\nبدء Fine-Tuning...")
  base_model.trainable = True
  fine_tune_at = int(len(base_model.layers) * 0.70)
  for layer in base_model.layers[:fine_tune_at]:
    layer.trainable = False

  model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=["accuracy"],
  )

  model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=HEAD_EPOCHS + FINE_TUNE_EPOCHS,
    initial_epoch=HEAD_EPOCHS,
    callbacks=callbacks,
  )

  # ==========================================
  # 7. تقييم النموذج على التحقق والاختبار
  # ==========================================
  val_loss, val_accuracy = model.evaluate(val_ds, verbose=0)
  print(f"\nدقة التحقق النهائية: {val_accuracy * 100:.2f}%")
  print(f"خسارة التحقق النهائية: {val_loss:.4f}")

  final_accuracy = float(val_accuracy)
  final_accuracy_source = "Validation"

  if TEST_DIR.exists():
    print("\nتحميل بيانات الاختبار (غير مرئية)...")
    test_ds = tf.keras.utils.image_dataset_from_directory(
      TEST_DIR,
      image_size=(IMG_HEIGHT, IMG_WIDTH),
      batch_size=BATCH_SIZE,
      shuffle=False,
    )

    test_class_names = test_ds.class_names
    if test_class_names != class_names:
      print("تحذير: ترتيب الفئات في مجلد الاختبار يختلف عن التدريب.")
      print(f"فئات التدريب: {class_names}")
      print(f"فئات الاختبار: {test_class_names}")

    test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)
    test_loss, test_accuracy = model.evaluate(test_ds, verbose=0)
    print(f"دقة الاختبار (بيانات غير مرئية): {test_accuracy * 100:.2f}%")
    print(f"خسارة الاختبار (بيانات غير مرئية): {test_loss:.4f}")

    final_accuracy = float(test_accuracy)
    final_accuracy_source = "Unseen Test"

    y_true, y_pred = collect_predictions(model, test_ds)
    report_data = print_classification_report(y_true, y_pred, class_names)

    output_payload = {
      "class_names": class_names,
      "validation_metrics": {
        "accuracy": float(val_accuracy),
        "loss": float(val_loss),
      },
      "test_metrics": {
        "accuracy": float(test_accuracy),
        "loss": float(test_loss),
      },
      "classification": report_data,
    }

    TEST_REPORT_JSON_PATH.write_text(
      json.dumps(output_payload, ensure_ascii=False, indent=2),
      encoding="utf-8",
    )

    txt_lines = [
      "Test Evaluation Report",
      "======================",
      f"Validation accuracy: {val_accuracy * 100:.2f}%",
      f"Validation loss: {val_loss:.4f}",
      f"Test accuracy: {test_accuracy * 100:.2f}%",
      f"Test loss: {test_loss:.4f}",
      "",
      "Confusion Matrix:",
      str(np.asarray(report_data["confusion_matrix"])),
      "",
      "Classification Report:",
      str(report_data["text_report"]),
    ]
    TEST_REPORT_TXT_PATH.write_text("\n".join(txt_lines), encoding="utf-8")

    print(f"\nتم حفظ تقرير الاختبار في: {TEST_REPORT_JSON_PATH}")
    print(f"تم حفظ التقرير النصي في: {TEST_REPORT_TXT_PATH}")
  else:
    print(f"\nمجلد الاختبار غير موجود: {TEST_DIR}")
    print("أنشئه لتقييم النموذج على بيانات غير مرئية بشكل صحيح.")

  # ==========================================
  # 8. حفظ النموذج النهائي
  # ==========================================
  model.save(MODEL_PATH)
  print(f"\nتم حفظ النموذج النهائي في: {MODEL_PATH}")
  print(f"وأفضل نسخة أثناء التدريب في: {BEST_MODEL_PATH}")
  print(f"Final Model Accuracy ({final_accuracy_source}): {final_accuracy * 100:.2f}%")


