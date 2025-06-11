import os, requests, logging, base64
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from ml_model import predict_crop
from weather_service import WeatherService
from werkzeug.utils import secure_filename
from weed_detection import WeedDetector
from disease_detection import DiseaseDetector
import numpy as np
import pickle
import sklearn
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# create the app
app = Flask(__name__)
app.secret_key = "Sandy@143"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models and forms
from models import User, users
from forms import LoginForm, SignupForm

# Initialize services
weather_service = WeatherService()

# Initialize the weed detector
ROBOFLOW_API_KEY = "wcb7iCJxgVbF3XXI4agu"  # Replace with your actual API key
weed_detector = WeedDetector(ROBOFLOW_API_KEY)
disease_detector = DiseaseDetector(ROBOFLOW_API_KEY)

# Load yield prediction models
models_path = Path(__file__).parent / 'models'
dtr = pickle.load(open(models_path / 'dtr.pkl', 'rb'))
preprocessor = pickle.load(open(models_path / 'preprocessor.pkl', 'rb'))

import pandas as pd

# Load the dataset
df = pd.read_csv(Path(__file__).parent / 'crop_yield_prediction_dataset/yield_df.csv')

# Get unique values for dropdowns
AREAS = sorted(df['Area'].unique().tolist())
ITEMS = sorted(df['Item'].unique().tolist()) 
YEARS = sorted(df['Year'].unique().tolist())

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/api/weather')
@login_required
def get_weather():
    try:
        city = request.args.get('city')
        if not city:
            return jsonify({'success': False, 'error': 'City parameter is required'}), 400

        weather_data = weather_service.get_weather(city)
        return jsonify({'success': True, 'weather': weather_data})
    except Exception as e:
        logging.error(f"Weather API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/weather/forecast')
@login_required
def get_weather_forecast():
    try:
        city = request.args.get('city')
        if not city:
            return jsonify({'success': False, 'error': 'City parameter is required'}), 400

        forecast_data = weather_service.get_forecast(city)
        return jsonify({'success': True, 'forecast': forecast_data})
    except Exception as e:
        logging.error(f"Weather API error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()  # Move this up
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = form.email.data
            password = form.password.data

        user = users.get(email)
        if user and user.check_password(password):
            login_user(user)
            logging.debug(f"Successful login for user: {email}")
            return jsonify({
                'success': True,
                'redirect': url_for('dashboard')
            })
        else:
            logging.debug(f"Failed login attempt for email: {email}")
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = SignupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.email.data in users:
                flash('Email already registered')
                logging.debug(f"Signup attempt with already registered email: {form.email.data}")
                return render_template('signup.html', form=form)

            user = User(form.email.data)
            user.set_password(form.password.data)
            users[user.email] = user
            logging.debug(f"Created new user: {user.email}")

            login_user(user)
            return redirect(url_for('dashboard'))
            
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/prediction')
@login_required
def prediction():
    return render_template('prediction.html')

@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.json
        result = predict_crop(
            nitrogen=data['nitrogen'],
            phosphorus=data['phosphorus'],
            potassium=data['potassium'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            ph=data['ph'],
            rainfall=data['rainfall']
        )
        return jsonify({'success': True, 'prediction': result})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/check-email', methods=['POST'])
def check_email():
    data = request.get_json()
    email = data.get('email')
    if email in users:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.errorhandler(404)
def not_found_error(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('index.html'), 500

@app.route('/detect-weeds', methods=['POST'])
@login_required
def detect_weeds():
    if 'plant-image' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    file = request.files['plant-image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    try:
        # Ensure temp directory exists
        temp_dir = os.path.join('static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded image temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        # Perform weed detection
        result = weed_detector.detect_weeds(temp_path)
        
        return jsonify({
            'success': True,
            'image_path': temp_path,
            'weed_data': result
        })

    except Exception as e:
        logging.error(f"Weed detection error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/weed-detection')
@login_required
def weed_detection():
    return render_template('weed_detection.html')

@app.route('/disease-detection')
@login_required
def disease_detection():
    return render_template('disease_detection.html')

@app.route('/detect-disease', methods=['POST'])
@login_required
def detect_disease():
    if 'plant-image' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    file = request.files['plant-image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    try:
        # Ensure temp directory exists
        temp_dir = os.path.join('static', 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded image temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        # Perform disease detection
        result = disease_detector.detect_disease(temp_path)
        
        return jsonify({
            'success': True,
            'image_path': temp_path,
            'disease_data': result
        })

    except Exception as e:
        logging.error(f"Disease detection error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/session-login', methods=['POST'])
def session_login():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'error': 'Authorization header missing'}), 401

    try:
        # Verify Firebase ID token
        id_token = auth_header.split(' ')[1]
        
        # Get email from request body
        email = request.json.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        # Create or get user
        if email not in users:
            user = User(email=email)
            users[email] = user
            logging.debug(f"Created new Firebase user: {email}")
        else:
            user = users[email]
            logging.debug(f"Found existing user: {email}")

        # Login user and create session
        login_user(user, remember=True)
        logging.debug(f"Successfully logged in user: {email}")
        
        return jsonify({
            'success': True,
            'redirect': url_for('dashboard'),
            'email': email
        })

    except Exception as e:
        logging.error(f"Session login error: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Authentication failed. Please try again.'
        }), 401

@app.route('/yield-prediction')
@login_required
def yield_prediction():
    return render_template('yield_prediction.html',
                         areas=AREAS,
                         items=ITEMS,
                         years=YEARS)

@app.route("/predict-yield", methods=['POST'])
@login_required
def predict_yield():
    try:
        if request.method == 'POST':
            # Get form data
            year = int(request.form['Year'])
            rainfall = float(request.form['average_rain_fall_mm_per_year'])
            pesticides = float(request.form['pesticides_tonnes'])
            temperature = float(request.form['avg_temp'])
            area = request.form['Area']
            item = request.form['Item']

            # Validate inputs
            if area not in AREAS:
                raise ValueError(f"Invalid area selection: {area}")
            if item not in ITEMS:
                raise ValueError(f"Invalid item selection: {item}") 
            if year not in YEARS:
                raise ValueError(f"Invalid year selection: {year}")
                
            # Create features array
            features = pd.DataFrame({
                'Year': [year],
                'average_rain_fall_mm_per_year': [rainfall],
                'pesticides_tonnes': [pesticides], 
                'avg_temp': [temperature],
                'Area': [area],
                'Item': [item]
            })
            
            # Transform features and make prediction
            transformed_features = preprocessor.transform(features)
            prediction = dtr.predict(transformed_features).reshape(1, -1)
            
            logging.debug(f"Yield prediction made for {area}, {item}: {prediction[0][0]}")
            
            return render_template('yield_prediction.html', 
                                prediction=prediction[0][0],
                                areas=AREAS,
                                items=ITEMS,
                                years=YEARS)
            
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        flash(str(ve))
    except Exception as e:
        logging.error(f"Yield prediction error: {str(e)}")
        flash('Error making prediction. Please check your inputs.')
        
    return render_template('yield_prediction.html',
                         areas=AREAS,
                         items=ITEMS, 
                         years=YEARS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)