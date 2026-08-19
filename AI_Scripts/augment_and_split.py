import os
import shutil
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
import uuid

SOURCE_DIR = 'test_data'
BASE_OUTPUT_DIR = 'dataset'
TRAIN_DIR = os.path.join(BASE_OUTPUT_DIR, 'train')
TEST_DIR = os.path.join(BASE_OUTPUT_DIR, 'test')

TARGET_COUNT_PER_CLASS = 1500 # We will augment each class until it has 1500 images
TEST_SPLIT = 0.20 # 20% of images go to test set

# Setup Data Augmentation
datagen = ImageDataGenerator(
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

def augment_and_split():
    # Clear output directory if it exists
    if os.path.exists(BASE_OUTPUT_DIR):
        shutil.rmtree(BASE_OUTPUT_DIR)
    
    os.makedirs(TRAIN_DIR, exist_ok=True)
    os.makedirs(TEST_DIR, exist_ok=True)
    
    classes = [d for d in os.listdir(SOURCE_DIR) if os.path.isdir(os.path.join(SOURCE_DIR, d))]
    
    for cls in classes:
        print(f"Processing class: {cls}...")
        source_class_dir = os.path.join(SOURCE_DIR, cls)
        train_class_dir = os.path.join(TRAIN_DIR, cls)
        test_class_dir = os.path.join(TEST_DIR, cls)
        
        os.makedirs(train_class_dir, exist_ok=True)
        os.makedirs(test_class_dir, exist_ok=True)
        
        # Read all images
        images = [f for f in os.listdir(source_class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            print(f"No images found in {source_class_dir}. Skipping.")
            continue
            
        print(f"  Found {len(images)} original images.")
        
        # Shuffle original images
        np.random.shuffle(images)
        
        # Calculate split
        test_count = max(1, int(len(images) * TEST_SPLIT)) if len(images) > 0 else 0
        test_images = images[:test_count]
        train_images = images[test_count:]
        
        print(f"  Splitting {len(images)} original images into {len(train_images)} train and {len(test_images)} test.")
        
        # 1. Move test images directly to final test directory
        for img_name in test_images:
            src_path = os.path.join(source_class_dir, img_name)
            dst_name = f"orig_{img_name}"
            dst_path = os.path.join(test_class_dir, dst_name)
            shutil.copy2(src_path, dst_path)
            
        # 2. Move train images directly to final train directory and load them for augmentation
        train_img_arrays = []
        for img_name in train_images:
            src_path = os.path.join(source_class_dir, img_name)
            dst_name = f"orig_{img_name}"
            dst_path = os.path.join(train_class_dir, dst_name)
            shutil.copy2(src_path, dst_path)
            
            try:
                img = load_img(src_path, target_size=(224, 224))
                x = img_to_array(img)
                x = x.reshape((1,) + x.shape)
                train_img_arrays.append(x)
            except Exception as e:
                print(f"  Error loading {src_path}: {e}")
                
        # 3. Augment ONLY train images to reach TARGET_COUNT_PER_CLASS
        train_augmented_needed = max(0, TARGET_COUNT_PER_CLASS - len(train_images))
        
        if train_augmented_needed > 0 and train_img_arrays:
            print(f"  Augmenting {train_augmented_needed} new images from the train set to reach {TARGET_COUNT_PER_CLASS}...")
            generated = 0
            while generated < train_augmented_needed:
                orig_img = train_img_arrays[np.random.randint(0, len(train_img_arrays))]
                # Generate augmentation directly into train directory
                next(datagen.flow(orig_img, batch_size=1, save_to_dir=train_class_dir, save_prefix='aug', save_format='jpeg'))
                generated += 1
                
    print("Done enhancing and splitting dataset!")

if __name__ == '__main__':
    augment_and_split()
