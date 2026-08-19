import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.metrics import AUC
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# Absolute path logic for reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, '..', 'Backend', 'config.json')
MODEL_PATH = os.path.join(BASE_DIR, '..', 'Final_Model', 'currency.h5')
# Evaluating directly on the NEW simplified path (Dataset/test/)
TEST_DIR = os.path.join(BASE_DIR, '..', 'Dataset', 'test')

def main():
    if not os.path.exists(TEST_DIR):
        print(f"Error: Test directory '{TEST_DIR}' not found. Please run augment_and_split.py first.")
        return

    # Load Configuration
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
            labels = config_data.get('model_labels', {})
            class_names_dict = {int(k): v for k, v in labels.items()}
    except Exception as e:
        print(f"Could not load config: {e}")
        class_names_dict = {0: 'Fake', 1: 'Other', 2: 'Real'}

    # Load Model
    print("Loading retrained model...")
    dependencies = {'auc_roc': AUC}
    model = load_model(MODEL_PATH, custom_objects=dependencies)

    # Prepare Dataset
    print(f"Loading testing dataset from {TEST_DIR}...")
    test_dataset = tf.keras.preprocessing.image_dataset_from_directory(
        TEST_DIR,
        labels='inferred',
        label_mode='int',
        image_size=(224, 224),
        batch_size=32,
        shuffle=False # VERY IMPORTANT for matching predictions to true labels
    )

    class_names = test_dataset.class_names
    print(f"Detected subdirectories (classes): {class_names}")

    true_labels = []
    predictions = []

    print("Running inference on unseen test data...")
    for images, labels in test_dataset:
        # Preprocess same as app.py (division by 255.0)
        processed_images = images / 255.0
        preds = model.predict(processed_images, verbose=0)
        pred_classes = np.argmax(preds, axis=1)
        
        true_labels.extend(labels.numpy())
        predictions.extend(pred_classes)

    display_labels = [class_names_dict.get(i, class_names[i]) for i in range(len(class_names))]

    print("\nClassification Report (Real-World Performance):")
    print(classification_report(true_labels, predictions, target_names=display_labels))

    print("Generating Confusion Matrix Plot...")
    cm = confusion_matrix(true_labels, predictions)

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=display_labels, yticklabels=display_labels)
    plt.title('True Evaluation Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    output_path = os.path.join(BASE_DIR, '..', 'Frontend', 'static', 'matrix_evaluated.png')
    plt.savefig(output_path, dpi=300)
    print(f"\n✅ Accurate Confusion Matrix successfully saved as '{output_path}'")

if __name__ == "__main__":
    main()
