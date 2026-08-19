import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.metrics import AUC
from tensorflow.keras.optimizers import Adam

# 1. Load the buggy model
model_path = os.path.join('Final_Model', 'currency.h5')
print("Loading existing model...")
model = load_model(model_path, custom_objects={'auc_roc': AUC})

# 2. Setup Data Augmentation (This makes the AI smarter by rotating/zooming images)
train_datagen = ImageDataGenerator(
    rescale=1./255, # Keep scaling to 0-1 as originally trained
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

# 3. Load the local `Dataset/train` folder (enhanced and balanced dataset)
train_dir = os.path.join('Dataset', 'train')
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(224, 224),
    batch_size=16, # Increased batch size due to more data
    class_mode='categorical'
)

# 4. Re-compile the model with a tiny learning rate so it doesn't forget past knowledge
model.compile(optimizer=Adam(learning_rate=0.0001), 
              loss='categorical_crossentropy', 
              metrics=['accuracy', AUC(name='auc_roc')])

# 5. Fine-tune! Force the AI to learn the specific features of these images
print("Retraining model on new balanced dataset (Dataset/train) for 2 epochs...")
model.fit(train_generator, epochs=2)

# 6. Save the smarter model
print("Saving improved model back to currency.h5...")
model.save(model_path)
print("Done!")
