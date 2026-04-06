from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import requests
import os
from pymongo import MongoClient
from datetime import datetime
import sys
import os as os_module
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Intelligence-Module'))


from Orchestrator import Pipeline_Orchestrator

app = Flask(__name__)
app.secret_key = "dev-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None

# Initialize CSRF protection
csrf = CSRFProtect(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MongoDB connection for storing AI test results
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['cicd_app']
ai_tests_collection = mongo_db['ai_tests']

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
SUPPORTED_EXT = ['.py', '.c', '.cpp', '.java']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API backend url (when running in containers, the service name 'api' is resolvable)
API_URL = os.environ.get("API_URL", "http://api:3000")

# Database Model
class Employee(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50), nullable=False)  # admin or developer
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id))

# Make csrf_token available in all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# Forms
class LoginForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=1, max=50)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    position = SelectField('Position', choices=[('admin', 'Admin'), ('developer', 'Developer')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

@app.route("/", methods=["GET", "POST"])
@login_required
@csrf.exempt
def index():
    samples = []
    if os.path.isdir(SAMPLES_DIR):
        samples = [f for f in os.listdir(SAMPLES_DIR) if os.path.splitext(f)[1] in SUPPORTED_EXT]

    if request.method == "POST":
        print(f"\n{'='*60}")
        print(f"POST REQUEST RECEIVED")
        print(f"{'='*60}")
        print(f"Request form keys: {list(request.form.keys())}")
        print(f"Request files keys: {list(request.files.keys())}")
        print(f"Request files: {request.files}")
        
        # sample selected
        sample = request.form.get("sample")
        if sample:
            print(f"Sample provided: {sample}")
            path = os.path.join(SAMPLES_DIR, sample)
            # Run AI pipeline instead of basic compilation
            try:
                # Change to Intelligence-Module directory for relative paths
                original_cwd = os.getcwd()
                intelligence_dir = os.path.join(BASE_DIR, 'Intelligence-Module')
                os.chdir(intelligence_dir)
                
                # Use relative path from Intelligence-Module
                relative_path = '../samples/' + sample
                pipeline = Pipeline_Orchestrator(relative_path)
                result = pipeline.run_pipeline()
                output = pipeline.get_output_string(result)
                
                # Change back
                os.chdir(original_cwd)
                
                # Read the generated JSON results
                json_results_path = os.path.join(BASE_DIR, 'Intelligence-Module', 'Stage1', 'Tests', 'Test_Cases.json')
                json_results = {}
                if os.path.exists(json_results_path):
                    with open(json_results_path, 'r') as f:
                        json_results = json.load(f)
                
                return render_template("result.html", filename=sample, result=result, json_results=json_results, output=output)
            except Exception as e:
                os.chdir(original_cwd)  # Make sure to change back even on error
                flash(f"Error running AI analysis: {str(e)}")
                print(f"Error: {str(e)}")
                return redirect(url_for("index"))

        # file uploaded
        print(f"Looking for 'file' in request.files...")
        if 'file' in request.files:
            uploaded = request.files['file']
            print(f"File object found: {uploaded}")
            print(f"Filename: {uploaded.filename}")
            print(f"File size: {len(uploaded.read()) if uploaded else 'N/A'}")
            uploaded.seek(0)  # Reset file pointer after reading
            
            if uploaded and uploaded.filename and uploaded.filename != '':
                filename = os.path.basename(uploaded.filename)  # Sanitize filename
                print(f"Processing uploaded file: {filename}")
                
                # Ensure uploads directory exists
                intelligence_upload_dir = os.path.join(BASE_DIR, 'Intelligence-Module', 'uploads')
                print(f"Uploads directory: {intelligence_upload_dir}")
                os.makedirs(intelligence_upload_dir, exist_ok=True)
                
                save_path = os.path.join(intelligence_upload_dir, filename)
                print(f"Saving to: {save_path}")
                
                try:
                    uploaded.save(save_path)
                    print(f"File saved successfully")
                    
                    if os.path.exists(save_path):
                        file_size = os.path.getsize(save_path)
                        print(f"File exists at {save_path} - Size: {file_size} bytes")
                    else:
                        print(f"ERROR: File does not exist at {save_path}")
                except Exception as e:
                    print(f"ERROR saving file: {str(e)}")
                    flash(f"Error saving file: {str(e)}")
                    return redirect(url_for("index"))
                
                try:
                    print("Starting AI analysis...")
                    # Change to Intelligence-Module directory for relative paths
                    original_cwd = os.getcwd()
                    intelligence_dir = os.path.join(BASE_DIR, 'Intelligence-Module')
                    os.chdir(intelligence_dir)
                    
                    # Use relative path from Intelligence-Module
                    relative_path = 'uploads/' + filename
                    print(f"Running pipeline with path: {relative_path}")
                    pipeline = Pipeline_Orchestrator(relative_path)
                    result = pipeline.run_pipeline()
                    output = pipeline.get_output_string(result)
                    print("AI analysis completed")
                    
                    # Change back
                    os.chdir(original_cwd)
                    
                    # Read the generated JSON results
                    json_results_path = os.path.join(BASE_DIR, 'Intelligence-Module', 'Stage1', 'Tests', 'Test_Cases.json')
                    json_results = {}
                    if os.path.exists(json_results_path):
                        with open(json_results_path, 'r') as f:
                            json_results = json.load(f)
                    
                    return render_template("result.html", filename=filename, result=result, json_results=json_results, output=output)
                except Exception as e:
                    os.chdir(original_cwd)  # Make sure to change back even on error
                    print(f"Error running AI analysis: {str(e)}")
                    flash(f"Error running AI analysis: {str(e)}")
                    return redirect(url_for("index"))
            else:
                print(f"File check failed - uploaded: {uploaded}, filename: {repr(uploaded.filename) if uploaded else 'None'}")
        else:
            print(f"'file' not in request.files")

        print(f"No file uploaded or sample selected - redirecting")
        flash("No file uploaded or sample selected")
        return redirect(url_for("index"))

    return render_template("index.html", samples=samples)


@app.route("/webhooks", methods=["GET"])
@login_required
def show_webhooks():
    """Fetch recent webhook entries from the Node API and render them."""
    try:
        resp = requests.get(f"{API_URL}/webhooks", timeout=5)
        if resp.status_code == 200:
            entries = resp.json()
        else:
            entries = []
            flash(f"API returned status {resp.status_code}")
    except Exception as e:
        entries = []
        flash(f"Failed to reach API at {API_URL}: {e}")

    return render_template("webhooks.html", entries=entries)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(employee_id=form.employee_id.data).first()
        if employee and employee.check_password(form.password.data):
            login_user(employee)
            return redirect(url_for('dashboard'))
        flash('Invalid employee ID or password')
    return render_template('login.html', form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if Employee.query.filter_by(employee_id=form.employee_id.data).first():
            flash('Employee ID already exists')
            return redirect(url_for('signup'))
        employee = Employee(employee_id=form.employee_id.data, name=form.name.data, position=form.position.data)
        employee.set_password(form.password.data)
        db.session.add(employee)
        db.session.commit()
        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    # For now, admin and developer dashboards are the same
    return render_template('dashboard.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    # Bind to 0.0.0.0 so the app is reachable from outside the container
    app.run(debug=True, host="0.0.0.0", port=5000)