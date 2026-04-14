from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
import bcrypt
import requests
import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'Intelligence-Module'))


from Orchestrator import Pipeline_Orchestrator

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None

# Initialize CSRF protection
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MongoDB connection for storing users, uploaded files, and AI test results
mongo_uri = (
    os.environ.get('MONGO_URI')
    or os.environ.get('MONGODB_URI')
    or os.environ.get('MONGO_DB')
    or 'mongodb://localhost:27017/cicd_app'
)

# MongoDB connection with fallback to local/mock database
mongo_client = None
mongo_db = None
employees_collection = None
ai_tests_collection = None

try:
    mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
    mongo_client.server_info()
    mongo_db = mongo_client.get_default_database()
    if mongo_db is None:
        mongo_db = mongo_client['cicd_app']
    employees_collection = mongo_db['employees']
    ai_tests_collection = mongo_db['ai_tests']
    print("✓ MongoDB connected successfully")
except Exception as e:
    print(f"⚠ Warning: MongoDB connection failed: {e}")
    print("⚠ Running in offline mode - limited functionality")

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
SUPPORTED_EXT = ['.py', '.c', '.cpp', '.java']
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API backend url (when running in containers, the service name 'api' is resolvable)
API_URL = os.environ.get("API_URL", "http://api:3000")

class Employee(UserMixin):
    def __init__(self, _id, employee_id, username, name, position, password_hash):
        self.id = str(_id)
        self.employee_id = employee_id
        self.username = username
        self.name = name
        self.position = position
        self.password_hash = password_hash

    @classmethod
    def from_document(cls, doc):
        if not doc:
            return None
        return cls(doc['_id'], doc['employee_id'], doc.get('username', ''), doc.get('name', ''), doc.get('position', 'developer'), doc['password_hash'])

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


def get_employee_by_username(username):
    if employees_collection is None:
        return None
    doc = employees_collection.find_one({'username': username})
    return Employee.from_document(doc)


def get_employee_by_objectid(object_id):
    try:
        doc = employees_collection.find_one({'_id': ObjectId(object_id)})
        return Employee.from_document(doc)
    except Exception:
        return None


@login_manager.user_loader
def load_user(user_id):
    return get_employee_by_objectid(user_id)


def store_test_run(employee, test_type, filename, source_path, result, output, json_results, file_contents=None):
    try:
        record = {
            'employee_id': getattr(employee, 'employee_id', None),
            'employee_name': getattr(employee, 'name', None),
            'position': getattr(employee, 'position', None),
            'test_type': test_type,
            'filename': filename,
            'source_path': source_path,
            'result': result,
            'output': output,
            'json_results': json_results,
            'file_contents': file_contents,
            'created_at': datetime.utcnow()
        }
        if ai_tests_collection is not None:
            ai_tests_collection.insert_one(record)
    except Exception as e:
        print(f"Warning: failed to store AI test run in MongoDB: {e}")

# Make csrf_token available in all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=50)])
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    position = SelectField('Position', choices=[('admin', 'Admin'), ('developer', 'Developer')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class ChangePasswordForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Account')

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
            try:
                original_cwd = os.getcwd()
                intelligence_dir = os.path.join(BASE_DIR, 'Intelligence-Module')
                os.chdir(intelligence_dir)

                relative_path = '../samples/' + sample
                pipeline = Pipeline_Orchestrator(relative_path)
                result = pipeline.run_pipeline()
                output = pipeline.get_output_string(result)

                os.chdir(original_cwd)

                json_results_path = os.path.join(BASE_DIR, 'Intelligence-Module', 'Stage1', 'Tests', 'Test_Cases.json')
                json_results = {}
                if os.path.exists(json_results_path):
                    with open(json_results_path, 'r') as f:
                        json_results = json.load(f)

                sample_contents = None
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8', errors='replace') as f:
                            sample_contents = f.read()
                    except Exception as e:
                        print(f"Warning: failed to read sample contents: {e}")

                store_test_run(current_user, 'sample', sample, path, result, output, json_results, sample_contents)
                return render_template("result.html", filename=sample, result=result, json_results=json_results, output=output)
            except Exception as e:
                os.chdir(original_cwd)
                flash(f"Error running AI analysis: {str(e)}")
                print(f"Error: {str(e)}")
                return redirect(url_for("index"))

        if 'file' in request.files:
            uploaded = request.files['file']
            print(f"File object found: {uploaded}")
            print(f"Filename: {uploaded.filename}")

            if uploaded and uploaded.filename and uploaded.filename != '':
                filename = os.path.basename(uploaded.filename)
                print(f"Processing uploaded file: {filename}")

                try:
                    uploaded.seek(0)
                    file_contents = uploaded.read().decode('utf-8', errors='replace')
                    uploaded.seek(0)
                except Exception:
                    file_contents = None

                intelligence_upload_dir = os.path.join(BASE_DIR, 'Intelligence-Module', 'uploads')
                os.makedirs(intelligence_upload_dir, exist_ok=True)

                save_path = os.path.join(intelligence_upload_dir, filename)
                print(f"Saving to: {save_path}")

                try:
                    uploaded.save(save_path)
                except Exception as e:
                    print(f"ERROR saving file: {str(e)}")
                    flash(f"Error saving file: {str(e)}")
                    return redirect(url_for("index"))

                try:
                    print("Starting AI analysis...")
                    original_cwd = os.getcwd()
                    intelligence_dir = os.path.join(BASE_DIR, 'Intelligence-Module')
                    os.chdir(intelligence_dir)

                    relative_path = 'uploads/' + filename
                    print(f"Running pipeline with path: {relative_path}")
                    pipeline = Pipeline_Orchestrator(relative_path)
                    result = pipeline.run_pipeline()
                    output = pipeline.get_output_string(result)
                    print("AI analysis completed")

                    os.chdir(original_cwd)

                    json_results_path = os.path.join(BASE_DIR, 'Intelligence-Module', 'Stage1', 'Tests', 'Test_Cases.json')
                    json_results = {}
                    if os.path.exists(json_results_path):
                        with open(json_results_path, 'r') as f:
                            json_results = json.load(f)

                    store_test_run(current_user, 'upload', filename, save_path, result, output, json_results, file_contents)
                    return render_template("result.html", filename=filename, result=result, json_results=json_results, output=output)
                except Exception as e:
                    os.chdir(original_cwd)
                    print(f"Error running AI analysis: {str(e)}")
                    flash(f"Error running AI analysis: {str(e)}")
                    return redirect(url_for("index"))
            else:
                print(f"File check failed - uploaded: {uploaded}, filename: {repr(uploaded.filename) if uploaded else 'None'}")
                flash("No valid file uploaded")
                return redirect(url_for("index"))
        else:
            print(f"No file in request.files")

        print(f"No file uploaded or sample selected - redirecting")
        flash("No file uploaded or sample selected")
        return redirect(url_for("index"))

    return render_template("index.html", samples=samples)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index') if current_user.position != 'admin' else url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        employee = get_employee_by_username(form.username.data)
        if employee and employee.check_password(form.password.data):
            login_user(employee)
            return redirect(url_for('index') if employee.position != 'admin' else url_for('admin_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        if employees_collection is None:
            flash('Database not available')
            return redirect(url_for('signup'))
        if get_employee_by_username(form.username.data):
            flash('Username already exists')
            return redirect(url_for('signup'))

        # Generate employee_id
        last_employee = employees_collection.find_one(sort=[('employee_id', -1)])
        employee_id = (last_employee['employee_id'] if last_employee else 0) + 1

        password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        employee_doc = {
            'employee_id': employee_id,
            'username': form.username.data,
            'name': form.name.data,
            'position': form.position.data,
            'password_hash': password_hash,
            'created_at': datetime.utcnow()
        }
        employees_collection.insert_one(employee_doc)

        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.position != 'admin':
        return redirect(url_for('index'))
    # Get all employees
    if employees_collection is None:
        employees = []
    else:
        employees = list(employees_collection.find({}, {'_id': 0}))
    return render_template('admin_dashboard.html', employees=employees)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect')
            return redirect(url_for('settings'))
        # Update name
        update_data = {'name': form.name.data}
        # Update password if provided
        if form.new_password.data:
            new_hash = bcrypt.hashpw(form.new_password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            update_data['password_hash'] = new_hash
        if employees_collection is not None:
            employees_collection.update_one(
                {'username': current_user.username},
                {'$set': update_data}
            )
            # Update current_user name
            current_user.name = form.name.data
            flash('Account updated successfully')
        else:
            flash('Database not available')
        return redirect(url_for('settings'))
    # Pre-fill name
    form.name.data = current_user.name
    return render_template('settings.html', form=form)


@app.route("/trigger-ci", methods=["POST"])
@login_required
@csrf.exempt
def trigger_ci():
    """Trigger GitHub Actions workflow to run CI/CD pipeline"""
    try:
        # Get GitHub credentials from environment variables
        github_token = os.environ.get('GITHUB_TOKEN')
        github_repo = os.environ.get('GITHUB_REPO', 'your-username/your-repo')  # Format: owner/repo
        workflow_file = os.environ.get('WORKFLOW_FILE', 'deploy.yml')
        
        if not github_token:
            flash("GitHub token not configured. Please set GITHUB_TOKEN environment variable.")
            return redirect(url_for("index"))
        
        # GitHub API endpoint to trigger workflow dispatch
        url = f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow_file}/dispatches"
        
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        payload = {
            'ref': 'main'  # Change to your main branch
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 204:
            flash("✓ CI/CD pipeline triggered successfully! Check GitHub Actions for progress.", "success")
            # Store CI trigger event in database
            if ai_tests_collection is not None:
                ai_tests_collection.insert_one({
                    'employee_id': current_user.employee_id,
                    'username': current_user.username,
                    'test_type': 'ci_trigger',
                    'timestamp': datetime.now(),
                    'status': 'triggered',
                    'github_repo': github_repo,
                    'workflow': workflow_file
                })
            print(f"✓ CI pipeline triggered by {current_user.username}")
        else:
            error_msg = f"Failed to trigger CI pipeline: {response.status_code} - {response.text}"
            flash(error_msg, "error")
            print(f"Error: {error_msg}")
        
        return redirect(url_for("index"))
    
    except requests.exceptions.Timeout:
        flash("Request timeout while triggering CI pipeline. Please try again.", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error triggering CI pipeline: {str(e)}", "error")
        print(f"Error: {str(e)}")
        return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    # Bind to 0.0.0.0 so the app is reachable from outside the container
    app.run(debug=True, host="0.0.0.0", port=5000)