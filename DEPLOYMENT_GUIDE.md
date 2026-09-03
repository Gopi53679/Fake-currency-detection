# 🚀 Deployment Guide: Fake Indian Currency Detection

This project is now configured for direct deployment to Cloud PaaS providers (**Render**, **Railway**, and **Hugging Face Spaces**). Follow any of the options below to get your **live shareable public URL**.

---

## ⚠️ Important Note on RAM & Model Size
- The deep learning model (`Final_Model/currency.h5`) is **~250 MB**.
- When loaded by TensorFlow, the application typically consumes **~800 MB to 1.2 GB of RAM**.
- We configured Gunicorn with **`--workers 1 --threads 2`** to keep memory usage minimal.
- **Recommendations**:
  - **Render**: The free tier provides 512 MB RAM. If Render crashes due to memory limits (Exit code 137 / OOM), upgrade to the **Starter Plan** ($7/mo with 1GB RAM) or use **Railway** / **Hugging Face Spaces**.
  - **Hugging Face Spaces**: **100% Free with 16 GB RAM**, which handles TensorFlow models with zero memory issues.
  - **Railway**: Provides generous RAM limits and pay-per-usage.

---

## Option 1: Deploy on Render (Recommended)

### Step 1: Push Changes to GitHub
Open your terminal in this repository and push the new deployment files:
```bash
git add .
git commit -m "Configure production deployment (Dockerfile, Procfile, wsgi.py)"
git push origin main
```

### Step 2: Connect to Render
1. Go to [Render.com](https://render.com) and Sign In (use your GitHub account).
2. Click **New +** in the top navigation and select **Web Service**.
3. Under **Connect a repository**, choose `Fake-currency-detection`.
4. Configure the settings:
   - **Name**: `fake-currency-detection` (or your preferred name)
   - **Region**: Choose closest to you (e.g., Singapore / Oregon / Frankfurt)
   - **Language / Environment**: **Docker** (Render will automatically detect our `Dockerfile`)
   - **Instance Type**: 
     - Try **Free** (512MB RAM) first, OR select **Starter** (1GB RAM) if it runs out of memory.
5. In **Environment Variables**, add:
   - `SECRET_KEY`: any random secure string (e.g. `currency_detection_prod_secret_2026`)
   - `FLASK_DEBUG`: `False`
6. Click **Deploy Web Service**.

### Step 3: Get Your Shareable Link
- Render will start building the Docker container and loading the model.
- Once the log shows `Application startup complete`, your website URL will be displayed at the top left under your project name, for example:
  ```
  https://fake-currency-detection-xxxx.onrender.com
  ```
- **Copy this link** and share it with anyone!

---

## Option 2: Deploy on Railway

1. Go to [Railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `Fake-currency-detection`.
4. Railway will automatically detect the `Dockerfile` and start building.
5. Go to the project **Settings** tab → Under **Networking**, click **Generate Domain**.
6. Railway will give you a public link like:
   ```
   https://fake-currency-detection-production.up.railway.app
   ```
7. Anyone can open this link on their phone, laptop, or tablet.

---

## Option 3: Deploy on Hugging Face Spaces (100% Free with 16 GB RAM)

Because this is a Machine Learning / AI model, Hugging Face Spaces is one of the best free platforms:

1. Create a free account on [Hugging Face](https://huggingface.co/).
2. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
3. Name your space (e.g., `fake-currency-detector`).
4. Select **Docker** as the Space SDK and choose **Blank**.
5. Push your code to the Hugging Face Space Git repository:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/fake-currency-detector
   git push hf main
   ```
6. Your live web app will be available at:
   ```
   https://YOUR_USERNAME-fake-currency-detector.hf.space
   ```
   *(Or embedded directly inside Hugging Face).*

---

## 🛠️ Included Production Files Overview

| File | Purpose |
|------|---------|
| [Backend/app.py](file:///Backend/app.py) | Configured host binding (`0.0.0.0`), dynamic `$PORT`, auto database creation. |
| [wsgi.py](file:///wsgi.py) | Top-level WSGI production entry point for Gunicorn. |
| [Dockerfile](file:///Dockerfile) | Container configuration with Python 3.8, OpenCV/Pillow system libraries, and Gunicorn. |
| [Procfile](file:///Procfile) | Web process command for PaaS buildpacks (`gunicorn wsgi:app`). |
| [render.yaml](file:///render.yaml) | Blueprint configuration for 1-click deployment on Render. |
| [runtime.txt](file:///runtime.txt) | Pins Python 3.8.18 for platforms using native buildpacks. |
| [.dockerignore](file:///.dockerignore) | Excludes large datasets and cache files from upload context. |
