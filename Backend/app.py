"""
Deep CNN-powered Fake Indian Currency Detection System
Back-end Logic (Flask + TensorFlow)
"""

import os
import logging
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.metrics import AUC
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import json
from datetime import datetime
import uuid
from urllib.parse import urlparse
from flask_wtf.csrf import CSRFProtect

# Configure Login & Monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            static_folder='../Frontend/static', 
            template_folder='../Frontend/templates')
app.secret_key = os.environ.get('SECRET_KEY', 'fyp_secure_secret_key_2024')
csrf = CSRFProtect(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # 10MB Upload Limit
db_path = os.path.normpath(os.path.join(BASE_DIR, '..', 'Database', 'fyp_database.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_color = db.Column(db.String(10), nullable=True, default="primary")
    scans = db.relationship('ScanLog', backref='author', lazy=True)

class ScanLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    prediction = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    date_scanned = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_vars():
    """Make recent scans and current time available globally to all templates."""
    recent_scans = []
    if current_user.is_authenticated:
        recent_scans = ScanLog.query.filter_by(user_id=current_user.id).order_by(ScanLog.date_scanned.desc()).all()
    
    return dict(recent_scans=recent_scans, now=datetime.now())

# Create tables if not exist within app context (Managed by Flask-Migrate)
# with app.app_context():
#     db.create_all()

# Model Configuration & Labelling
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
MODEL_PATH = os.path.join(BASE_DIR, '..', 'Final_Model', 'currency.h5')
dependencies = {'auc_roc': AUC}

# Load Configuration
try:
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        labels = config_data.get('model_labels', {})
        # Convert keys to int for mapping
        verbose_name = {int(k): v for k, v in labels.items()}
        error_msgs = config_data.get('error_messages', {})
except Exception as e:
    logger.error(f"Failed to load config.json: {e}")
    verbose_name = {0: 'Fake', 1: 'Other', 2: 'Real'}
    error_msgs = {"not_currency": "Error: Not a Currency Note!"}

# Global Model Loading (loads on startup)
model = None
try:
    logger.info(f"Loading system model from {MODEL_PATH}...")
    model = load_model(MODEL_PATH, custom_objects=dependencies)
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"CRITICAL: Model loading failed! Application will run in maintenance mode. Error: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_label(img_path):
    """Process input image and return (label, confidence_score)"""
    if model is None:
        return "Error: AI Engine Offline", 0.0
        
    logger.info(f"Inference started for: {img_path}")
    try:
        test_image = image.load_img(img_path, target_size=(224, 224))
        test_image = image.img_to_array(test_image) / 255.0
        test_image = test_image.reshape(1, 224, 224, 3)

        predict_x = model.predict(test_image)
        classes_x = np.argmax(predict_x, axis=1)
        confidence = np.max(predict_x) * 100
        
        result = verbose_name.get(classes_x[0], "NOT CURRENCY")
        
        # Consistent All-Caps Output
        if result == 'Real':
            result = "REAL"
        elif result == 'Fake':
            result = "FAKE"
        else:
            result = "NOT CURRENCY"
            
        logger.info(f"Prediction result: {result} ({confidence:.2f}%)")
        return result, round(confidence, 2)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        return "Error: Processing Failed", 0.0

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

# Application Routes
@app.route("/")
@app.route("/first")
def first():
    return render_template('first.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)  # type: ignore
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('upswd')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('index')
            return redirect(next_page)
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
            
    return render_template('login.html')

@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('first'))

@app.route("/index", methods=['GET', 'POST'])
@login_required
def index():
    return render_template("index.html")

@app.route("/submit", methods=['GET', 'POST'])
@login_required
def get_output():
    if request.method == 'POST':
        img = request.files.get('my_image')
        if not img or img.filename == '':
            flash("No image selected for upload.", "warning")
            return redirect(url_for('index'))

        if img and allowed_file(img.filename):
            # Generate a unique filename to prevent namespace collisions
            unique_id = uuid.uuid4().hex[:8]  # type: ignore
            filename = f"{current_user.id}_{unique_id}_{secure_filename(img.filename)}"
            # Save using absolute path for reliability
            img_path = os.path.join(BASE_DIR, "..", "Frontend", "static", "tests", filename).replace('\\', '/')
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            img.save(img_path)

            predict_result, confidence_score = predict_label(img_path)
                
            # Log the scan to the database
            scan_log = ScanLog(filename=filename, prediction=predict_result, confidence=float(confidence_score), user_id=current_user.id, date_scanned=datetime.now())  # type: ignore
            db.session.add(scan_log)
            db.session.commit()
                
            return redirect(url_for('view_result', 
                                    prediction=predict_result, 
                                    filename=filename, 
                                    score=confidence_score))
        else:
            flash("Invalid file type. Please upload a PNG, JPG, or JPEG.", "danger")
            return redirect(url_for('index'))
                               
    return redirect(url_for('index'))

@app.route("/view_result")
@login_required
def view_result():
    prediction = request.args.get('prediction')
    filename = request.args.get('filename')
    score = request.args.get('score', 'N/A')
    
    if not prediction or not filename:
        return redirect(url_for('index'))
        
    return render_template("prediction.html", 
                           prediction=prediction, 
                           filename=filename, 
                           score=score,
                           is_view_only=True)

@app.route("/clear_history", methods=['POST'])
@login_required
def clear_history():
    """Delete all scan logs and associated image files for the current user."""
    try:
        # Fetch scan logs to get filenames before deleting from DB
        logs = ScanLog.query.filter_by(user_id=current_user.id).all()
        for log in logs:
            file_path = os.path.join(BASE_DIR, "..", "Frontend", "static", "tests", log.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                
        # Efficient batch delete from DB
        ScanLog.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return {"success": True, "message": "Scan history cleared successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error clearing history: {e}")
        return {"success": False, "message": "Failed to clear history."}, 500

@app.route("/delete_scan/<int:scan_id>", methods=['POST'])
@login_required
def delete_scan(scan_id):
    """Delete a specific scan record and its image file for the current user."""
    try:
        scan = ScanLog.query.get_or_404(scan_id)
        if scan.user_id != current_user.id:
            return {"success": False, "message": "Unauthorized deletion attempt."}, 403
        
        # Delete the physical file
        file_path = os.path.join(BASE_DIR, "..", "Frontend", "static", "tests", scan.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        db.session.delete(scan)
        db.session.commit()
        return {"success": True, "message": "Scan deleted successfully."}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting scan {scan_id}: {e}")
        return {"success": False, "message": "Failed to delete scan."}, 500

@app.route("/performance")
@login_required
def performance():
    return render_template('performance.html')

@app.route("/chart")
@login_required
def chart():
    scans = ScanLog.query.filter_by(user_id=current_user.id).all()
    # Case-sensitive fix to match database storage ("REAL", "FAKE")
    real_count = sum(1 for s in scans if s.prediction == 'REAL')
    fake_count = sum(1 for s in scans if s.prediction == 'FAKE')
    # Include 'NOT CURRENCY' and potential error strings
    error_count = sum(1 for s in scans if s.prediction == 'NOT CURRENCY' or s.prediction.startswith('Error'))
    total_scans = len(scans)
    
    return render_template('chart.html', 
                           real_count=real_count,
                           fake_count=fake_count,
                           error_count=error_count,
                           total_scans=total_scans)

@app.errorhandler(404)
def page_not_found(e):
    flash("The page you're looking for was not found.", "info")
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    flash("An internal server error occurred. Please try again later.", "danger")
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(e):
    flash("File is too large. Max size is 5MB.", "warning")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Running with debug=True for development tracking
    app.run(debug=True)
