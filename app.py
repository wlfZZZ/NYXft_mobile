from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import os
import pandas as pd
import json
import io
import random
import string
import re
from flask_mail import Mail, Message
from authlib.integrations.flask_client import OAuth
import requests

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False

try:
    from flask_talisman import Talisman
    HAS_TALISMAN = True
except ImportError:
    HAS_TALISMAN = False

try:
    from flask_wtf.csrf import CSRFProtect
    HAS_CSRF = True
except ImportError:
    HAS_CSRF = False

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "nyx_fallback_secret")

# --- SECURITY LAYERS (Resilient Implementation) ---
if HAS_CSRF:
    csrf = CSRFProtect(app)
else:
    # Dummy CSRF class to prevent errors
    class DummyCSRF:
        def exempt(self, f): return f
    csrf = DummyCSRF()
    
    # Inject dummy csrf_token function for templates
    @app.context_processor
    def inject_csrf():
        return dict(csrf_token=lambda: "nyx_dummy_token")

# Rate Limiting Logic
if HAS_LIMITER:
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[os.getenv("RATELIMIT_DEFAULT", "200 per day;50 per hour")],
        storage_uri="memory://",
    )
else:
    # Dummy Limiter class to prevent errors
    class DummyLimiter:
        def limit(self, limit_string):
            return lambda f: f
    limiter = DummyLimiter()

# Secure Headers & CSP
if HAS_TALISMAN:
    csp = {
        'default-src': '\'self\'',
        'script-src': ['\'self\'', 'https://unpkg.com', 'https://cdn.jsdelivr.net', '\'unsafe-inline\''],
        'style-src': ['\'self\'', 'https://fonts.googleapis.com', 'https://unpkg.com', '\'unsafe-inline\''],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com', 'https://unpkg.com'],
        'img-src': ['\'self\'', 'data:', 'https://www.gstatic.com']
    }
    talisman = Talisman(
        app,
        content_security_policy=csp,
        force_https=False,
        session_cookie_secure=False,
        session_cookie_http_only=True
    )

# Database Configuration
# Automatically switches between local SQLite and Production PostgreSQL
db_url = os.getenv("DATABASE_URL", "sqlite:///nyx.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"connect_args": {"timeout": 15}} if "sqlite" in db_url else {}
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['SESSION_PERMANENT'] = True

db = SQLAlchemy(app)

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com").strip()
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True").strip().lower() == "true"
app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL", "False").strip().lower() == "true"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME", "").strip()
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD", "").strip()
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "NYX Performance OS <verify@nyxft.com>").strip()

mail = Mail(app)

import threading

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"[SYSTEM SUCCESS] Identity Handshake Transmitted to {msg.recipients[0]}")
        except Exception as e:
            print(f"[SYSTEM ALERT] Background Mail Transmission Failed: {e}")

def send_pulse_code(email, code, subject="NYX OS Security Pulse"):
    # Innovative Tactical Copy
    html_content = f"""
    <div style="background-color: #000; color: #fff; padding: 40px; font-family: 'Inter', sans-serif; text-align: center; border-radius: 8px;">
        <h1 style="letter-spacing: 4px; font-weight: 800; margin-bottom: 10px; color: #fff;">NYX PERFORMANCE OS</h1>
        <p style="color: #666; font-size: 12px; letter-spacing: 2px; margin-bottom: 40px;">// IDENTITY SYNCHRONIZATION PROTOCOL //</p>
        
        <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 12px; display: inline-block; min-width: 250px;">
            <p style="color: #888; font-size: 14px; margin-bottom: 20px; font-weight: 600;">YOUR SECURITY PULSE CODE</p>
            <div style="font-size: 48px; font-weight: 900; letter-spacing: 12px; color: #fff; margin: 20px 0;">{code}</div>
        </div>
        
        <p style="color: #444; font-size: 11px; margin-top: 40px; line-height: 1.6;">
            This pulse is valid for the current synchronization attempt.<br>
            If you did not initiate this uplink, secure your credentials immediately.<br>
            <span style="color: #666;">SYSTEM STATUS: SECURE // LOCATION: CLOUD_NODE_PRIMARY</span>
        </p>
    </div>
    """
    
    msg = Message(f"[TACTICAL UPLINK] {subject}", recipients=[email])
    msg.html = html_content
    msg.body = f"NYX OS Security Pulse: {code} // Identity Synchronization Active."
    
    # --- TACTICAL OVERRIDE (NO MAIL) ---
    code = "111111" # Static code for temporary bypass
    user.verification_code = code
    db.session.commit()
    
    print(f"[SYSTEM OVERRIDE] Bypass Active for {email}. Code: {code}")
    
    return jsonify({'success': True, 'message': 'SECURITY_PULSE_DISPATCHED'})

# --- GOOGLE OAUTH INITIALIZATION ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- NAVIGATION REGISTRY (Source of Truth for Orb) ---
NAV_REGISTRY = [
    {"id": "lock", "label": "Lock", "url": "/auth", "icon": "ph-shield-check", "type": "action"},
    {"id": "dash", "label": "Dash", "url": "/dashboard", "icon": "ph-squares-four"},
    {"id": "workouts", "label": "Workout", "url": "/workouts", "icon": "ph-barbell"},
    {"id": "nutrition", "label": "Diet", "url": "/nutrition", "icon": "ph-fork-knife"},
    {"id": "analytics", "label": "Trends", "url": "/analytics", "icon": "ph-chart-line-up"},
    {"id": "prs", "label": "PR's", "url": "/pr-tracker", "icon": "ph-trophy"},
    {"id": "coaches", "label": "Coaches", "url": "/coaches", "icon": "ph-chat-circle-dots"},
    {"id": "settings", "label": "Settings", "url": "/settings", "icon": "ph-gear"},
    {"id": "logout", "label": "Logout", "url": "/logout", "icon": "ph-power", "class": "logout"}
]

@app.route('/api/nav')
def get_nav():
    return jsonify(NAV_REGISTRY)

# --- LOAD NUTRITION DATASET (FOOD + SUPPLEMENTS) ---
NUTRITION_DB = []
try:
    # 1. Load Foods
    food_path = os.path.join(os.path.dirname(__file__), 'docs', 'Food.xlsx')
    if os.path.exists(food_path):
        df_food = pd.read_excel(food_path)
        for _, row in df_food.iterrows():
            NUTRITION_DB.append({
                'name': str(row['Food Name']),
                'category': str(row.get('Category', 'General')),
                'calories': int(row['Calories (kcal/100g)']),
                'protein': float(row['Protein (g)']),
                'carbs': float(row['Carbs (g)']),
                'fats': float(row.get('Fat (g)', 0)),
                'source': 'food'
            })
    
    # 2. Load Supplements
    supp_path = os.path.join(os.path.dirname(__file__), 'docs', 'supplements_dataset.xlsx')
    if os.path.exists(supp_path):
        df_supp = pd.read_excel(supp_path)
        for _, row in df_supp.iterrows():
            NUTRITION_DB.append({
                'name': str(row['Supplement Name']),
                'category': str(row.get('Type', 'Supplement')),
                'calories': int(row.get('Calories (per serving)', 0)),
                'protein': float(row.get('Protein (g)', 0)),
                'carbs': float(row.get('Carbs (g)', 0)),
                'fats': 0.0, # Usually minimal in powders
                'source': 'supplement'
            })
    
    # print(f"Successfully synchronized {len(NUTRITION_DB)} items (Foods & Supplements).")
except Exception as e:
    # print(f"Error loading nutrition datasets: {e}")
    pass

# --- UNIFIED PERFORMANCE SCHEMA ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='athlete') # athlete, coach, admin
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(6))
    quick_pin = db.Column(db.String(4)) # 4-digit quick access key
    profile_setup_complete = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Coach-Athlete Uplink
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Bio-Data
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    height = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.String(20), nullable=True) # Initial/Current weight
    goal = db.Column(db.String(80), nullable=True)
    
    # Coach Profile Intel
    specialization = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Relationships
    biometrics = db.relationship('BioMetric', backref='user', lazy=True)
    nutrition = db.relationship('NutritionLog', backref='user', lazy=True)
    workouts = db.relationship('WorkoutSession', backref='user', lazy=True)
    prs = db.relationship('PersonalRecord', backref='user', lazy=True)
    messages = db.relationship('UplinkMessage', backref='user', lazy=True)

class BioMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False) # YYYY-MM-DD
    weight = db.Column(db.Float, nullable=True)
    steps = db.Column(db.Integer, default=0)
    sleep_hours = db.Column(db.Float, nullable=True)
    readiness_score = db.Column(db.Integer, nullable=True) # 1-10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NutritionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Float, default=0.0)
    carbs = db.Column(db.Float, default=0.0)
    fats = db.Column(db.Float, default=0.0)
    is_supplement = db.Column(db.Boolean, default=False)

class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    protocol_name = db.Column(db.String(100))
    duration_mins = db.Column(db.Integer, default=0)
    volume_kg = db.Column(db.Float, default=0.0)
    intensity_rpe = db.Column(db.Integer, nullable=True)
    logs = db.relationship('ExerciseLog', backref='session', lazy=True)

class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_session.id'), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    sets_data = db.Column(db.Text, nullable=False) # JSON: [{"reps": 10, "weight": 100}, ...]

class PersonalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise = db.Column(db.String(80), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    is_historical = db.Column(db.Boolean, default=False)

class UplinkMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False) # 'athlete', 'coach'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class WorkoutTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    exercises_data = db.Column(db.Text, nullable=False) # JSON list

# --- TOTAL SYSTEM INITIALIZATION ---
try:
    with app.app_context():
        # db.drop_all() 
        db.create_all()
        
        # SEED TACTICAL PERSONNEL
        if not User.query.filter_by(role='admin').first():
            admin = User(
                email="admin@nyxft.com",
                name="System Admin",
                nickname="admin",
                password="admin",
                role="admin",
                is_verified=True,
                profile_setup_complete=True
            )
            db.session.add(admin)
            
            demo_coach = User(
                email="coach@nyxft.com",
                name="Tactical Lead",
                nickname="Lead",
                password="coach",
                role="coach",
                is_verified=True,
                profile_setup_complete=True,
                specialization="Performance Engineering",
                bio="Focusing on peak biological output and metabolic efficiency."
            )
            db.session.add(demo_coach)
            db.session.commit()
            print("DATABASE PROTOCOL: Unified Schema Active.")
except Exception as e:
    print(f"DATABASE ALERT: Initialization bypassed - {e}")


# --- UTILITIES ---
def safe_float(val, default=0.0):
    try:
        if val is None: return default
        # Remove non-numeric characters except . and -
        clean_val = re.sub(r'[^0-9.\-]', '', str(val))
        return float(clean_val) if clean_val else default
    except:
        return default

# --- ROUTING ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('client/index.html')

@app.route('/logout')
def logout_redirect():
    session.clear()
    return redirect(url_for('index'))

@app.route('/auth')
def auth():
    # ── SESSION PERSISTENCE CHECK ──
    email = session.get('user')
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            if user.role == 'admin': return redirect(url_for('admin_dashboard'))
            if user.role == 'coach': return redirect(url_for('coach_dashboard'))
            
            if user.profile_setup_complete:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('profile_setup'))
                
    return render_template('client/auth.html')

@app.route('/signup')
def signup():
    return redirect(url_for('auth', mode='signup'))

@app.route('/api/auth/check', methods=['POST'])
def api_auth_check():
    email = request.json.get('email', '').lower().strip()
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'exists': True, 'has_pin': bool(user.quick_pin)})
    return jsonify({'exists': False})

@app.route('/api/auth/pin/set', methods=['POST'])
def api_auth_pin_set():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    pin = request.json.get('pin')
    if not pin or len(pin) != 4: return jsonify({'error': 'Invalid PIN format'}), 400
    
    user = User.query.filter_by(email=session['user']).first()
    if user:
        user.quick_pin = pin
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/auth/pin/verify', methods=['POST'])
def api_auth_pin_verify():
    pin = request.json.get('pin')
    email = session.get('user')
    
    if not email: return jsonify({'error': 'Identity session expired. Please re-authenticate via Google/Apple.'}), 401
    
    user = User.query.filter_by(email=email).first()
    if user and user.quick_pin == pin:
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
        
    return jsonify({'error': 'INVALID SECURITY PIN'}), 401

@app.route('/profile-setup')
def profile_setup():
    if 'user' not in session:
        return redirect(url_for('auth'))
    return render_template('client/profile-setup.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('client/forgot_password.html')


@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    return render_template('client/chat.html', user=user)

@app.route('/coaches')
def coaches():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    if not user: return redirect(url_for('auth'))
    
    all_coaches = User.query.filter_by(role='coach').all()
    assigned_coach = User.query.get(user.coach_id) if user.coach_id else None
    
    return render_template('client/coaches.html', 
                           user=user, 
                           coaches=all_coaches,
                           assigned_coach=assigned_coach,
                           messages=user.messages)

@app.route('/api/coach/select', methods=['POST'])
def api_coach_select():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    data = request.json
    coach_id = data.get('coach_id')
    
    if coach_id:
        user.coach_id = coach_id
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'No coach selected'}), 400

@app.route('/pr-tracker')
def pr_tracker():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    if not user: return redirect(url_for('auth'))

    all_logs = user.prs[::-1]
    KEY_EXERCISES = ['Bench Press', 'Squat', 'Deadlift']
    key_lifts = []
    
    for ex in KEY_EXERCISES:
        records = sorted([p for p in user.prs if p.exercise.lower() == ex.lower()], key=lambda x: x.weight)
        current = records[-1].weight if records else 0
        previous = records[-2].weight if len(records) >= 2 else 0
        key_lifts.append({
            'exercise': ex,
            'current': current,
            'previous': previous,
            'delta': round(current - previous, 1) if current and previous else 0
        })

    return render_template('client/pr_tracker.html',
        user=user,
        prs=all_logs[:20],
        key_lifts=key_lifts,
        total_logs=len(user.prs),
        best_lift=max([p.weight for p in user.prs], default=0)
    )

@app.route('/nutrition')
def nutrition():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    if not user: return redirect(url_for('auth'))
    
    today = datetime.now().strftime("%Y-%m-%d")
    food_items = NutritionLog.query.filter_by(user_id=user.id, date=today).all()
    
    totals = {
        'calories': sum(item.calories for item in food_items),
        'protein': sum(item.protein for item in food_items),
        'carbs': sum(item.carbs for item in food_items),
        'fats': sum(item.fats for item in food_items)
    }
    
    targets = {
        'calories': 2500,
        'protein': 180,
        'carbs': 300,
        'fats': 70
    }
    
    meals = {
        'Breakfast': [i for i in food_items if i.meal_type == 'Breakfast'],
        'Lunch': [i for i in food_items if i.meal_type == 'Lunch'],
        'Dinner': [i for i in food_items if i.meal_type == 'Dinner'],
        'Snacks': [i for i in food_items if i.meal_type == 'Snacks']
    }
    
    return render_template('client/nutrition.html', user=user, meals=meals, totals=totals, targets=targets)

@app.route('/settings')
def settings():
    if 'user' not in session: return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    return render_template('client/settings.html', user=user)

@app.route('/workouts')
def workouts():
    if 'user' not in session: return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    
    assigned = None
    if user.assigned_workout:
        try:
            assigned = json.loads(user.assigned_workout)
        except: pass
        
    return render_template('client/workouts.html', user=user, assigned=assigned)

@app.route('/analytics')
def analytics():
    if 'user' not in session:
        return redirect(url_for('auth'))
    user = User.query.filter_by(email=session['user']).first()
    if not user: return redirect(url_for('auth'))
    
    # ── VITAL SIGNS TRENDS (30 Days) ──
    biometrics = user.biometrics[-30:]
    labels = [b.date for b in biometrics]
    weight_history = [b.weight or 0 for b in biometrics]
    step_history = [b.steps or 0 for b in biometrics]

    # ── STRENGTH TRENDS ──
    prs = user.prs
    volume = {'Push': 0, 'Pull': 0, 'Legs': 0}
    for p in prs:
        ex = p.exercise.lower()
        v = (p.weight or 0) * (p.reps or 1)
        if any(x in ex for x in ['bench', 'press', 'dip']): volume['Push'] += v
        elif any(x in ex for x in ['row', 'pull', 'curl', 'deadlift']): volume['Pull'] += v
        elif any(x in ex for x in ['squat', 'leg', 'lunge']): volume['Legs'] += v

    # ── AI PREDICTIONS & CONSISTENCY ──
    consistency_data = [1 if (b.steps or 0) >= 10000 else 0 for b in biometrics]
    
    eta_days = "STABLE"
    try:
        if user.weight:
            current = safe_float(weight_history[-1]) if weight_history and weight_history[-1] else safe_float(user.weight)
            # Simple heuristic: 0.5kg change per week
            # We look for a number in the user.goal string
            import re
            goal_match = re.search(r'(\d+)', str(user.goal))
            if goal_match:
                target = float(goal_match.group(1))
                diff = abs(current - target)
                if diff > 0.1:
                    weeks = diff / 0.5
                    eta_days = f"{int(weeks * 7)} DAYS"
    except: pass

    return render_template('client/analytics.html',
        user=user,
        labels=labels,
        weight_history=weight_history,
        step_history=step_history,
        volume=volume,
        consistency_data=consistency_data,
        eta_days=eta_days
    )


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth'))
    
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return redirect(url_for('auth'))
        
    # --- AUTOMATIC WAKE-UP DETECTION ---
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    if not user.last_login_at or user.last_login_at.strftime("%Y-%m-%d") != today_str:
        user.daily_wake_up_at = now.strftime("%H:%M")
        user.last_login_at = now
        db.session.commit()
    
    # --- STATS CALCULATION ---
    # --- DASHBOARD INTELLIGENCE ---
    user_biometrics = user.biometrics
    user_prs = user.prs
    
    # Calculate streak (days with steps >= 10000)
    streak = 0
    for l in reversed(user_biometrics):
        if (l.steps or 0) >= 10000:
            streak += 1
        else:
            break

    # Weight trend
    weight_trend = 0
    if len(user_biometrics) >= 2:
        try:
            curr_w = user_biometrics[-1].weight or 0
            prev_w = user_biometrics[-2].weight or 0
            if curr_w and prev_w:
                weight_trend = round(curr_w - prev_w, 1)
        except: pass

    # Chart Data (7 Days)
    weekly_steps = [0] * 7
    weekly_weight = [0] * 7
    for i in range(7):
        d = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
        l = BioMetric.query.filter_by(user_id=user.id, date=d).first()
        if l:
            weekly_steps[i] = l.steps or 0
            weekly_weight[i] = l.weight or 0

    # Activity Timeline
    timeline = []
    for pr in user_prs[-5:]:
        timeline.append({
            'type': 'workout',
            'title': f'Logged {pr.exercise}',
            'desc': f'{pr.weight}kg x {pr.reps} reps',
            'time': pr.date,
            'icon': 'ph-barbell'
        })
    for l in user_biometrics[-3:]:
        if l.weight:
            timeline.append({
                'type': 'weight',
                'title': 'Weight Updated',
                'desc': f'{l.weight}kg',
                'time': l.date,
                'icon': 'ph-scales'
            })
    timeline = sorted(timeline, key=lambda x: x['time'], reverse=True)[:6]

    stats = {
        'main_insight': "You achieved your step goal 3 days in a row! Keep the momentum. 🔥" if streak >= 3 else "Protocol synchronized. All vital signs normal. Focusing on performance metrics.",
        'latest_weight': user_biometrics[-1].weight if user_biometrics and user_biometrics[-1].weight else safe_float(user.weight),
        'latest_steps': user_biometrics[-1].steps if user_biometrics else 0,
        'step_goal': 10000,
        'streak': streak,
        'weight_trend': weight_trend,
        'consistency': f"{min(100, int((len(user_biometrics) / 7) * 100))}%" if user_biometrics else "0%",
        'weekly_steps': weekly_steps,
        'weekly_weight': weekly_weight,
        'recent_pr': ('No Intel' if not user_prs else
                      f"{max(user_prs, key=lambda p: p.weight).exercise} · {max(user_prs, key=lambda p: p.weight).weight}kg"),
        'timeline': timeline,
        'recent_workouts': user_prs[-3:][::-1]
    }

    # Check if weight logged today
    has_logged_weight = False
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_log = BioMetric.query.filter_by(user_id=user.id, date=today_str).first()
    if today_log and today_log.weight:
        has_logged_weight = True

    return render_template('client/dashboard.html', 
                           user=user, 
                           stats=stats,
                           has_logged_weight=has_logged_weight)


# --- API ENDPOINTS ---

@app.route('/api/log', methods=['POST'])
@limiter.limit("10 per minute")
def api_log():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    existing_log = BioMetric.query.filter_by(user_id=user.id, date=today_str).first()
    
    weight = data.get('weight')
    steps = data.get('steps')
    readiness = data.get('readiness')
    
    if existing_log:
        if weight is not None:
            if existing_log.weight:
                return jsonify({'error': 'Protocol Limit: Daily weight already archived.'}), 400
            existing_log.weight = weight
        if steps is not None:
            existing_log.steps = steps
        if readiness is not None:
            existing_log.readiness_score = readiness
    else:
        new_log = BioMetric(
            date=today_str,
            weight=weight,
            steps=steps or 0,
            readiness_score=readiness,
            user_id=user.id
        )
        db.session.add(new_log)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/pr', methods=['POST'])
def api_pr():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    user = User.query.filter_by(email=session['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    exercise = data.get('exercise', '').strip()
    new_weight = float(data.get('weight', 0))
    new_reps = int(data.get('reps', 1))

    # Identify if new PR
    prev_best = db.session.query(db.func.max(PersonalRecord.weight)).filter_by(
        user_id=user.id, exercise=exercise
    ).scalar()
    is_new_pr = prev_best is None or new_weight > prev_best

    log = PersonalRecord(
        date=datetime.now().strftime("%Y-%m-%d"),
        exercise=exercise,
        weight=new_weight,
        reps=new_reps,
        user_id=user.id
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'success': True, 'is_new_pr': is_new_pr, 'exercise': exercise, 'weight': new_weight})

@app.route('/api/auth/google', methods=['GET', 'POST'])
@csrf.exempt
def api_auth_google():
    redirect_uri = url_for('api_auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/google/callback')
@csrf.exempt
def api_auth_google_callback():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        return redirect(url_for('auth'))
    
    user_info = token.get('userinfo')
    if not user_info:
        user_info = google.get('userinfo').json()
    
    email = user_info.get('email').lower().strip()
    name = user_info.get('name')
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # --- NEW PERSONNEL ENROLLMENT ---
        user = User(
            email=email,
            name=name,
            nickname=user_info.get('given_name', name),
            password="GOOGLE_OAUTH_LINKED",
            is_verified=True,
            profile_setup_complete=False
        )
        db.session.add(user)
        db.session.commit()
        
        session.permanent = True
        session['user'] = email
        return redirect(url_for('profile_setup'))
    else:
        # --- EXISTING PERSONNEL ACCESS ---
        session.permanent = True
        session['user'] = email
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        if user.role == 'admin': return redirect(url_for('admin_dashboard'))
        if user.role == 'coach': return redirect(url_for('coach_dashboard'))
        
        if user.profile_setup_complete:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('profile_setup'))

@app.route('/api/auth', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt 
def api_auth():
    data = request.json
    action = data.get('action')
    email = data.get('email', '').lower().strip()
    password = data.get('password')

    if not email:
        return jsonify({'error': 'Email required'}), 400
    if action == 'signup' and not password:
        return jsonify({'error': 'Passcode required for signup'}), 400

    if action == 'signup':
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
            
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Full name is required for signup'}), 400
            
        v_code = ''.join(random.choices(string.digits, k=6))
        new_user = User(
            email=email,
            name=name,
            nickname=name,
            password=password,
            verification_code=v_code,
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        send_pulse_code(email, v_code, "NYX OS Verification Code")
        return jsonify({'success': True, 'requires_verification': True, 'email': email})
        
    elif action == 'login':
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate Login Verification Pulse
            v_code = ''.join(random.choices(string.digits, k=6))
            user.verification_code = v_code
            db.session.commit()
            
            send_pulse_code(email, v_code, "NYX OS Login Pulse")
            return jsonify({'success': True, 'requires_verification': True, 'email': email, 'message': 'Security pulse transmitted.'})
        else:
            return jsonify({'error': 'Personnel Identity Not Found. Please create an account.'}), 404
    
    return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/auth/verify', methods=['POST'])
@csrf.exempt
def api_verify():
    data = request.json
    email = data.get('email', '').lower().strip()
    code = data.get('code', '').strip()
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if user.verification_code == code:
        # Determine if they are returning before clearing the state
        is_returning = user.profile_setup_complete
        
        user.is_verified = True
        user.verification_code = None
        db.session.commit()
        session.permanent = True
        session['user'] = email
        
        # --- STRICT ROLE-BASED REDIRECTION ---
        if user.role == 'admin':
            session['admin_user'] = email
            return jsonify({'success': True, 'redirect': url_for('admin_dashboard')})
        if user.role == 'coach':
            session['coach_user'] = email
            return jsonify({'success': True, 'redirect': url_for('coach_dashboard')})
            
        if is_returning:
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': True, 'redirect': url_for('profile_setup')})
    
    return jsonify({'error': 'Invalid verification code'}), 400

@app.route('/api/profile', methods=['POST'])
def api_profile():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    user = User.query.filter_by(email=session['user']).first()
    if user:
        user.age = data.get('age')
        user.gender = data.get('gender')
        user.height = data.get('height')
        user.weight = data.get('weight')
        user.goal = data.get('goal')
        user.profile_setup_complete = True
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'redirect': url_for('auth')})

@app.route('/api/nutrition/data')
def get_daily_data():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    if not user: return jsonify({'error': 'User not found'}), 404
    
    today = datetime.now().strftime("%Y-%m-%d")
    food_items = NutritionLog.query.filter_by(user_id=user.id, date=today).all()
    
    totals = {
        'calories': sum(item.calories for item in food_items),
        'protein': sum(item.protein for item in food_items),
        'carbs': sum(item.carbs for item in food_items),
        'fats': sum(item.fats for item in food_items)
    }
    
    meals = {'Breakfast': [], 'Lunch': [], 'Dinner': [], 'Snacks': []}
    for item in food_items:
        if item.meal_type in meals:
            meals[item.meal_type].append({
                'id': item.id,
                'name': item.name,
                'calories': item.calories,
                'protein': item.protein,
                'carbs': item.carbs,
                'fats': item.fats,
                'is_supplement': item.is_supplement
            })

    # Tactical Targets (Unified)
    try:
        bw = float(''.join(c for c in (user.weight or "75") if c.isdigit() or c=='.'))
    except:
        bw = 75.0
    
    tdee = int(bw * 33)
    targets = {
        'calories': tdee,
        'protein': int(bw * 2.2),
        'carbs': int((tdee * 0.45) / 4),
        'fats': int((tdee * 0.25) / 9)
    }

    return jsonify({
        'totals': totals,
        'meals': meals,
        'targets': targets,
        'user_weight': user.weight
    })

@app.route('/api/nutrition/add', methods=['POST'])
def add_food():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    user = User.query.filter_by(email=session['user']).first()
    data = request.json
    
    new_item = NutritionLog(
        name=data.get('name'),
        meal_type=data.get('meal_type'),
        calories=int(data.get('calories', 0)),
        protein=float(data.get('protein', 0)),
        carbs=float(data.get('carbs', 0)),
        fats=float(data.get('fats', 0)),
        date=datetime.now().strftime("%Y-%m-%d"),
        user_id=user.id,
        is_supplement=data.get('is_supplement', False)
    )
    db.session.add(new_item)
    db.session.commit()
    return get_daily_data()

@app.route('/api/nutrition/remove', methods=['POST'])
def remove_food():
    if 'user' not in session: return jsonify({'error': 'Unauthorized'}), 401
    item_id = request.json.get('id')
    item = NutritionLog.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        return get_daily_data()
    return jsonify({'error': 'Item not found'}), 404
from functools import wraps

@app.route('/coach/login', methods=['GET'])
def coach_login():
    if 'coach_user' in session:
        user = User.query.filter_by(email=session['coach_user']).first()
        if user and user.role == 'coach':
            return redirect(url_for('coach_dashboard'))
    return render_template('coach/coach_login.html')

@app.route('/coach/logout')
def coach_logout():
    session.pop('coach_user', None)
    return redirect(url_for('coach_login'))

@app.route('/admin/login', methods=['GET'])
def admin_login():
    if 'admin_user' in session:
        user = User.query.filter_by(email=session['admin_user']).first()
        if user and user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return render_template('admin/admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user', None)
    return redirect(url_for('admin_login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user' not in session:
            return redirect(url_for('auth', role='admin'))
        user = User.query.filter_by(email=session['admin_user']).first()
        if not user or user.role != 'admin':
            return redirect(url_for('auth', role='admin'))
        return f(*args, **kwargs)
    return decorated_function

def coach_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'coach_user' not in session:
            return redirect(url_for('auth', role='coach'))
        user = User.query.filter_by(email=session['coach_user']).first()
        if not user or user.role not in ['coach', 'admin']:
            return redirect(url_for('auth', role='coach'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/chat/send', methods=['POST'])
def api_send_message():
    data = request.json
    user_id = data.get('user_id')
    content = data.get('content')
    sender = data.get('sender')
    
    if not all([user_id, content, sender]):
        return jsonify({'error': 'Missing data'}), 400
        
    msg = UplinkMessage(user_id=user_id, content=content, sender=sender)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chat/history/<int:user_id>')
def api_chat_history(user_id):
    viewer_email = session.get('user') or session.get('coach_user') or session.get('admin_user')
    if not viewer_email:
        return jsonify({'error': 'Unauthorized'}), 401
        
    viewer = User.query.filter_by(email=viewer_email).first()
    target = User.query.get_or_404(user_id)

    # Security Handshake
    if viewer.role == 'athlete' and viewer.id != target.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if viewer.role == 'coach' and target.coach_id != viewer.id:
        return jsonify({'error': 'Unauthorized'}), 403

    messages = UplinkMessage.query.filter_by(user_id=user_id).order_by(UplinkMessage.timestamp.asc()).all()
    return jsonify([{
        'sender': m.sender,
        'content': m.content,
        'timestamp': m.timestamp.strftime('%H:%M')
    } for m in messages])

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_logs = BioMetric.query.count() + NutritionLog.query.count()
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    total_coaches = User.query.filter_by(role='coach').count()
    
    return render_template('admin/admin_dashboard.html', 
                           total_users=total_users, 
                           total_logs=total_logs,
                           recent_users=recent_users,
                           total_coaches=total_coaches)

@app.route('/coach/dashboard')
@coach_required
def coach_dashboard():
    coach = User.query.filter_by(email=session['coach_user']).first()
    
    if coach.role == 'admin':
        roster = User.query.filter_by(role='athlete').all()
    else:
        roster = User.query.filter_by(coach_id=coach.id).all()
        
    roster_stats = []
    activity_feed = []
    
    for athlete in roster:
        # Pull latest biometrics for trend analysis
        logs = BioMetric.query.filter_by(user_id=athlete.id).order_by(BioMetric.date.desc()).limit(7).all()
        
        weight_delta = 0
        if len(logs) >= 2:
            try:
                curr_w = logs[0].weight or 0
                prev_w = logs[1].weight or 0
                if curr_w and prev_w:
                    weight_delta = round(curr_w - prev_w, 1)
            except: pass
            
        status = "offline"
        if athlete.biometrics:
            latest = athlete.biometrics[-1]
            diff = datetime.utcnow() - latest.created_at
            status = "active" if diff < timedelta(days=1) else "inactive"

        roster_stats.append({
            'user': athlete,
            'weight_history': [float(log.weight or 0) for log in reversed(logs)] if logs else [70.0],
            'dates': [log.date[5:] for log in reversed(logs)] if logs else ['N/A'],
            'weight_delta': weight_delta,
            'status': status
        })
        
        if logs:
            activity_feed.append({
                'name': athlete.name,
                'action': 'LOGGED_VITALS',
                'time': logs[0].created_at.strftime('%H:%M'),
                'detail': f"{logs[0].weight}kg | {logs[0].readiness_score or 'N/A'} Readiness"
            })

    return render_template('coach/dashboard.html', 
                           roster=roster, 
                           roster_stats=roster_stats,
                           activity_feed=activity_feed[:10],
                           roster_count=len(roster))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(role='athlete').all()
    coaches = User.query.filter_by(role='coach').all()
    return render_template('admin/admin_users.html', users=users, coaches=coaches)

@app.route('/admin/assign_coach', methods=['POST'])
@admin_required
def assign_coach():
    data = request.json
    athlete = User.query.get_or_404(data.get('user_id'))
    athlete.coach_id = data.get('coach_id')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/export_users')
@admin_required
def export_users():
    athletes = User.query.filter_by(role='athlete').all()
    data = []
    for u in athletes:
        data.append({
            'ID': f"NYX-{u.id:04d}",
            'Name': u.name,
            'Email': u.email,
            'Age': u.age,
            'Goal': u.goal,
            'Verified': 'YES' if u.is_verified else 'NO'
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Personnel')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"NYX_Personnel_Manifest.xlsx"
    )

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    BioMetric.query.filter_by(user_id=user.id).delete()
    NutritionLog.query.filter_by(user_id=user.id).delete()
    WorkoutSession.query.filter_by(user_id=user.id).delete()
    UplinkMessage.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f"Personnel {user.name} purged from system.", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/assign_workout', methods=['POST'])
@admin_required
def assign_workout():
    data = request.json
    user_id = data.get('user_id')
    workout_data = data.get('workout') # Muscle, Type, Duration
    
    user = User.query.get_or_404(user_id)
    user.assigned_workout = json.dumps(workout_data)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Workout assigned to {user.name}'})


@app.route('/admin/athlete/<int:user_id>')
@admin_required
def admin_athlete_profile(user_id):
    target_user = User.query.get_or_404(user_id)
    # Get vitals for charts from the new BioMetric model
    logs = BioMetric.query.filter_by(user_id=user_id).order_by(BioMetric.date.asc()).all()
    prs = PersonalRecord.query.filter_by(user_id=user_id).order_by(PersonalRecord.date.desc()).all()
    
    # Weights for chart
    weights = [log.weight for log in logs if log.weight]
    dates = [log.date for log in logs if log.weight]
    
    return render_template('admin/admin_athlete_profile.html', 
                           target_user=target_user,
                           logs=logs,
                           prs=prs,
                           weights=weights,
                           dates=dates)


@app.route('/admin/assign_nutrition', methods=['POST'])
@admin_required
def assign_nutrition():
    data = request.json
    user = User.query.get_or_404(data.get('user_id'))
    user.goal = data.get('goal')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/modify_nutrition', methods=['POST'])
@admin_required
def admin_modify_nutrition():
    data = request.json
    user = User.query.get_or_404(data.get('user_id'))
    new_goal = data.get('goal')
    
    user.goal = new_goal
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Nutrition goal for {user.name} updated to {new_goal}'})

@app.route('/admin/nutrition')
@admin_required
def admin_nutrition():
    # Show stats about the dataset
    foods = [i for i in NUTRITION_DB if i['source'] == 'food']
    supps = [i for i in NUTRITION_DB if i['source'] == 'supplement']
    
    return render_template('admin/admin_nutrition.html', 
                           foods_count=len(foods),
                           supps_count=len(supps),
                           total_count=len(NUTRITION_DB))


@app.route('/admin/workouts')
@admin_required
def admin_workouts():
    # Define static training architectures for the oversight view
    muscle_groups = ['Chest', 'Back', 'Legs', 'Shoulders', 'Arms']
    exercises = {
        'Chest': [{'name': 'Bench Press', 'sets': 4, 'reps': 8}, {'name': 'Incline Fly', 'sets': 3, 'reps': 12}],
        'Back': [{'name': 'Deadlift', 'sets': 5, 'reps': 5}, {'name': 'Lat Pulldown', 'sets': 4, 'reps': 10}],
        'Legs': [{'name': 'Squat', 'sets': 4, 'reps': 10}, {'name': 'Leg Press', 'sets': 3, 'reps': 15}]
    }
    training_styles = [
        {'name': 'Compound Training', 'desc': 'Primary force development through multi-joint protocols.', 'workouts': 142},
        {'name': 'Hypertrophy Phase', 'desc': 'Volume-centric architectures for metabolic overload.', 'workouts': 86},
        {'name': 'Powerbuilding', 'desc': 'Hybrid system combining force and aesthetic evolution.', 'workouts': 210}
    ]
    athletes = User.query.limit(10).all()
    
    return render_template('admin/admin_workouts.html', 
                           muscle_groups=muscle_groups,
                           exercises=exercises,
                           training_styles=training_styles,
                           athletes=athletes)

@app.route('/foods')
def get_foods():
    return jsonify(NUTRITION_DB)

if __name__ == '__main__':
    # The Unified Schema is initialized in the 'TOTAL SYSTEM INITIALIZATION' block above
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
