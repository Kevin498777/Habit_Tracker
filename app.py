# app.py - Versión completa con gestión de cookies
import os
import re
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, Response, jsonify, make_response
)
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave-secreta-predeterminada')

# -----------------------------
# MÉTRICAS PROMETHEUS
# -----------------------------
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total number of requests',
    ['method', 'endpoint']
)

EXCEPTIONS = Counter(
    'app_exceptions_total',
    'Total number of unhandled exceptions',
    ['endpoint', 'exception_type']
)

REQUEST_TIME = Summary(
    'app_request_processing_seconds',
    'Time spent processing request'
)

@app.errorhandler(Exception)
def catch_all(e):
    # Incrementa la métrica de excepciones y vuelve a lanzar la excepción
    try:
        EXCEPTIONS.labels(
            endpoint=request.path,
            exception_type=type(e).__name__
        ).inc()
    except Exception:
        # Evitar que la métrica rompa el manejo de excepciones
        pass
    # Re-lanzamos la excepción para que Flask la maneje normalmente (logs, etc.)
    raise e

@app.before_request
def before_request():
    # Contador de requests por método y endpoint
    try:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path
        ).inc()
    except Exception:
        pass
    
    # Verificar y configurar cookies para la solicitud actual
    setup_cookies()

@app.route("/metrics")
def metrics():
    """Endpoint de métricas para Prometheus"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# -----------------------------
# CONFIGURACIÓN DE MONGODB
# -----------------------------
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    client.admin.command('ping')
    print("OK - Conectado a MongoDB exitosamente!")
    
    db = client['habit_tracker']
    habits_collection = db['habits']
    users_collection = db['users']
    
except Exception as e:
    print(f"ERROR - Conectando a MongoDB: {e}")
    # En producción, continuar pero mostrar error claro
    habits_collection = None
    users_collection = None

# -----------------------------
# CONFIGURACIÓN DE COOKIES
# -----------------------------
class CookieConfig:
    # Configuración por defecto
    DEFAULT_SETTINGS = {
        'essential_cookies': True,      # Siempre activas
        'preference_cookies': True,     # Cookies de preferencias
        'analytics_cookies': True,      # Cookies analíticas
        'functional_cookies': True,     # Cookies de funcionalidad
        'third_party_cookies': False,   # Cookies de terceros
        'anonymous_data': True,         # Datos anónimos
        'same_site_cookies': True,      # Protección SameSite
        'data_retention': '730',        # 2 años por defecto
        'performance_cookies': True,    # Cookies de rendimiento
        'cookie_consent_given': False,  # Consentimiento dado
        'cookie_consent_date': None,    # Fecha de consentimiento
        'last_updated': None            # Última actualización
    }
    
    # Tiempos de expiración
    EXPIRATION = {
        'session': 0,                   # Duración de sesión
        'short_term': 86400,            # 1 día
        'medium_term': 2592000,         # 30 días
        'long_term': 31536000,          # 1 año
        'extended_term': 63072000       # 2 años
    }

def setup_cookies():
    """Configurar cookies basadas en preferencias del usuario"""
    # Solo configuramos cookies si el usuario ha dado consentimiento
    # o son cookies esenciales
    
    cookie_settings = get_cookie_settings()
    
    # Configurar cookie de sesión si el usuario está autenticado
    if 'user_id' in session:
        # Cookie esencial para sesión - HTTP Only, Secure, SameSite Strict
        @app.after_request
        def add_cookie_headers(response):
            response.set_cookie(
                'session_id',
                value=session['user_id'],
                httponly=True,
                secure=not app.debug,  # Secure solo en producción
                samesite='Strict',
                max_age=CookieConfig.EXPIRATION['medium_term']
            )
            
            # Cookie de preferencias si están habilitadas
            if cookie_settings.get('preference_cookies', True):
                response.set_cookie(
                    'user_preferences',
                    value=json.dumps(cookie_settings),
                    httponly=True,
                    secure=not app.debug,
                    samesite='Lax',
                    max_age=CookieConfig.EXPIRATION['long_term']
                )
            
            # Cookie analítica si está habilitada
            if cookie_settings.get('analytics_cookies', True):
                response.set_cookie(
                    'analytics_consent',
                    value='true',
                    httponly=False,  # Necesaria para JavaScript
                    secure=not app.debug,
                    samesite='Lax',
                    max_age=CookieConfig.EXPIRATION['extended_term']
                )
            
            # Cookie de CSRF para protección
            response.set_cookie(
                'csrf_token',
                value=generate_csrf_token(),
                httponly=True,
                secure=not app.debug,
                samesite='Strict',
                max_age=CookieConfig.EXPIRATION['short_term']
            )
            
            return response
    
    return None

def generate_csrf_token():
    """Generar token CSRF seguro"""
    import secrets
    return secrets.token_urlsafe(32)

def get_cookie_settings():
    """Obtener configuración de cookies del usuario"""
    # Primero verificar en la sesión
    if 'cookie_settings' in session:
        return session['cookie_settings']
    
    # Luego verificar en cookies del navegador
    cookie_settings_cookie = request.cookies.get('user_preferences')
    if cookie_settings_cookie:
        try:
            settings = json.loads(cookie_settings_cookie)
            session['cookie_settings'] = settings
            return settings
        except json.JSONDecodeError:
            pass
    
    # Devolver configuración por defecto
    return CookieConfig.DEFAULT_SETTINGS.copy()

def save_cookie_settings(settings):
    """Guardar configuración de cookies"""
    # Actualizar fecha de última modificación
    settings['last_updated'] = datetime.now()
    
    # Guardar en sesión
    session['cookie_settings'] = settings
    
    # Si el usuario está autenticado, guardar en base de datos
    if 'user_id' in session and users_collection:
        try:
            users_collection.update_one(
                {'_id': ObjectId(session['user_id'])},
                {'$set': {'cookie_settings': settings}}
            )
        except Exception as e:
            print(f"Error guardando configuración de cookies: {e}")
    
    return settings

# -----------------------------
# UTILIDADES / DECORADORES
# -----------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_csrf_token():
    """Validar token CSRF"""
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        csrf_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        cookie_token = request.cookies.get('csrf_token')
        
        if not csrf_token or not cookie_token or csrf_token != cookie_token:
            return False
    return True

# -----------------------------
# RUTAS PRINCIPALES
# -----------------------------
@app.route('/')
@REQUEST_TIME.time()
def index():
    """Página principal que muestra la lista de hábitos"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    habits = []
    today_completed = 0
    total_habits = 0
    completion_rate = 0.0
    week_completions = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if habits_collection is not None:
            habits = list(habits_collection.find(
                {'user_id': session['user_id']}
            ).sort('created_at', -1))
            
            today_completed = sum(1 for habit in habits if today in habit.get('completed_dates', []))
            total_habits = len(habits)
            
            # Calcular tasa de completado DE FORMA SEGURA
            if total_habits > 0:
                completion_rate = round((today_completed / total_habits) * 100, 1)
            else:
                completion_rate = 0.0
            
            # Calcular hábitos de esta semana
            week_dates = []
            for i in range(7):
                day = datetime.now() - timedelta(days=i)
                week_dates.append(day.strftime('%Y-%m-%d'))
            
            week_completions = 0
            for habit in habits:
                for date in habit.get('completed_dates', []):
                    if date in week_dates:
                        week_completions += 1
                        break
                        
        else:
            flash('Error de conexión con la base de datos', 'error')
    except Exception as e:
        print(f"Error en index: {e}")
        flash('Error al cargar los hábitos', 'error')
    
    # DEBUG: Verificar valores (opcional)
    print(f"DEBUG - total_habits: {total_habits}, today_completed: {today_completed}, completion_rate: {completion_rate}")
    
    return render_template('index.html', 
                        habits=habits, 
                        today_completed=today_completed,
                        total_habits=total_habits,
                        completion_rate=completion_rate,
                        week_completions=week_completions,
                        today=today)

# -----------------------------
# RUTAS DE AUTENTICACIÓN
# -----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido', 'error')
            return render_template('register.html')
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validaciones
        if not all([username, email, password, confirm_password]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html')
        
        if not is_valid_email(email):
            flash('Por favor ingresa un email válido', 'error')
            return render_template('register.html')
        
        # Verificar si el usuario o email ya existen
        try:
            existing_user = users_collection.find_one({
                '$or': [
                    {'username': username},
                    {'email': email}
                ]
            })
        except Exception as e:
            existing_user = None
            print(f"ERROR al buscar usuario existente: {e}")
        
        if existing_user:
            flash('El nombre de usuario o email ya están en uso', 'error')
            return render_template('register.html')
        
        # Crear nuevo usuario
        try:
            hashed_password = generate_password_hash(password)
            
            # Inicializar configuración de cookies para nuevo usuario
            cookie_settings = CookieConfig.DEFAULT_SETTINGS.copy()
            cookie_settings['cookie_consent_date'] = datetime.now()
            
            user = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'created_at': datetime.now(),
                'last_login': None,
                'cookie_settings': cookie_settings
            }
            
            result = users_collection.insert_one(user)
            
            # Iniciar sesión automáticamente
            session['user_id'] = str(result.inserted_id)
            session['username'] = username
            session['email'] = email
            session['cookie_settings'] = cookie_settings
            
            flash(f'¡Bienvenido {username}! Tu cuenta ha sido creada exitosamente.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            print(f"ERROR en register: {e}")
            flash('Error al crear la cuenta', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión de usuarios"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido', 'error')
            return render_template('login.html')
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'error')
            return render_template('login.html')
        
        try:
            # Verificar conexión a la base de datos
            if users_collection is None:
                flash('Error de conexión con la base de datos. Intenta nuevamente.', 'error')
                return render_template('login.html')
            
            # Buscar usuario por username o email
            user = users_collection.find_one({
                '$or': [
                    {'username': username},
                    {'email': username}
                ]
            })
            
            if user and check_password_hash(user['password'], password):
                try:
                    # Actualizar último login
                    users_collection.update_one(
                        {'_id': user['_id']},
                        {'$set': {'last_login': datetime.now()}}
                    )
                except Exception as e:
                    print(f"ERROR actualizando last_login: {e}")
                    # No interrumpimos el login si falla la actualización
                
                # Establecer sesión
                session['user_id'] = str(user['_id'])
                session['username'] = user['username']
                session['email'] = user['email']
                
                # Cargar configuración de cookies del usuario
                if 'cookie_settings' in user:
                    session['cookie_settings'] = user['cookie_settings']
                else:
                    session['cookie_settings'] = CookieConfig.DEFAULT_SETTINGS.copy()
                
                flash(f'¡Bienvenido de nuevo {user["username"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuario o contraseña incorrectos', 'error')
                
        except Exception as e:
            print(f"ERROR en login: {e}")
            flash('Error al procesar el inicio de sesión. Intenta nuevamente.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('login'))

# -----------------------------
# NUEVAS RUTAS PARA COOKIES
# -----------------------------
@app.route('/cookies-policy')
def cookies_policy():
    """Página de política de cookies"""
    return render_template('cookies_policy.html', current_date=datetime.now())

@app.route('/cookie-settings', methods=['GET', 'POST'])
def cookie_settings():
    """Página de configuración de cookies"""
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido', 'error')
            return redirect(url_for('cookie_settings'))
        
        # Procesar el formulario de configuración
        settings = {
            'preference_cookies': request.form.get('preference_cookies') == 'on',
            'analytics_cookies': request.form.get('analytics_cookies') == 'on',
            'functional_cookies': request.form.get('functional_cookies') == 'on',
            'third_party_cookies': request.form.get('third_party_cookies') == 'on',
            'anonymous_data': request.form.get('anonymous_data') == 'on',
            'same_site_cookies': request.form.get('same_site_cookies') == 'on',
            'data_retention': request.form.get('data_retention', '730'),
            'performance_cookies': request.form.get('performance_cookies') == 'on',
            'cookie_consent_given': True,
            'cookie_consent_date': datetime.now(),
            'essential_cookies': True  # Siempre activas
        }
        
        # Guardar configuración
        save_cookie_settings(settings)
        
        flash('Configuración de cookies guardada correctamente', 'success')
        return redirect(url_for('cookie_settings'))
    
    # Obtener configuración actual
    current_settings = get_cookie_settings()
    
    return render_template('cookie_settings.html', 
                          cookie_settings=current_settings)

@app.route('/save-cookie-settings', methods=['POST'])
def save_cookie_settings_route():
    """Endpoint AJAX para guardar configuración de cookies"""
    try:
        if not validate_csrf_token():
            return jsonify({'error': 'Token CSRF inválido'}), 403
        
        data = request.get_json()
        
        # Validar datos recibidos
        required_fields = ['preference_cookies', 'analytics_cookies', 
                          'functional_cookies', 'data_retention']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} faltante'}), 400
        
        # Crear configuración
        settings = {
            'preference_cookies': data['preference_cookies'],
            'analytics_cookies': data['analytics_cookies'],
            'functional_cookies': data['functional_cookies'],
            'third_party_cookies': data.get('third_party_cookies', False),
            'anonymous_data': data.get('anonymous_data', True),
            'same_site_cookies': data.get('same_site_cookies', True),
            'data_retention': data['data_retention'],
            'performance_cookies': data.get('performance_cookies', True),
            'cookie_consent_given': True,
            'cookie_consent_date': datetime.now(),
            'essential_cookies': True
        }
        
        # Guardar configuración
        save_cookie_settings(settings)
        
        return jsonify({
            'success': True,
            'message': 'Configuración guardada',
            'settings': settings
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cookies/consent', methods=['POST'])
def record_cookie_consent():
    """Registrar consentimiento de cookies"""
    try:
        if not validate_csrf_token():
            return jsonify({'error': 'Token CSRF inválido'}), 403
        
        data = request.get_json()
        consent_type = data.get('type', 'all')  # 'all', 'essential', 'custom'
        
        # Obtener configuración actual
        current_settings = get_cookie_settings()
        
        # Actualizar según el tipo de consentimiento
        if consent_type == 'all':
            current_settings.update({
                'preference_cookies': True,
                'analytics_cookies': True,
                'functional_cookies': True,
                'cookie_consent_given': True,
                'cookie_consent_date': datetime.now()
            })
        elif consent_type == 'essential':
            current_settings.update({
                'preference_cookies': False,
                'analytics_cookies': False,
                'functional_cookies': False,
                'cookie_consent_given': True,
                'cookie_consent_date': datetime.now()
            })
        
        # Guardar configuración
        save_cookie_settings(current_settings)
        
        # Registrar en métricas
        try:
            REQUEST_COUNT.labels(
                method='POST',
                endpoint='/api/cookies/consent'
            ).inc()
        except:
            pass
        
        return jsonify({
            'success': True,
            'message': f'Consentimiento {consent_type} registrado',
            'consent_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cookies/clear', methods=['POST'])
@login_required
def clear_cookies():
    """Eliminar cookies del usuario"""
    try:
        if not validate_csrf_token():
            return jsonify({'error': 'Token CSRF inválido'}), 403
        
        # Eliminar configuración de cookies
        if 'cookie_settings' in session:
            del session['cookie_settings']
        
        # Eliminar de la base de datos si existe
        if 'user_id' in session and users_collection:
            users_collection.update_one(
                {'_id': ObjectId(session['user_id'])},
                {'$unset': {'cookie_settings': ''}}
            )
        
        # Crear respuesta que elimine cookies del navegador
        response = jsonify({
            'success': True,
            'message': 'Cookies eliminadas correctamente'
        })
        
        # Eliminar cookies del navegador
        response.set_cookie('user_preferences', '', expires=0)
        response.set_cookie('analytics_consent', '', expires=0)
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# app.py - Secciones para las nuevas rutas

@app.route('/privacy-policy')
def privacy_policy():
    """Página de política de privacidad"""
    return render_template('privacy_policy.html', current_date=datetime.now())

@app.route('/terms-of-service')
def terms_of_service():
    """Página de términos y condiciones"""
    return render_template('terms_conditions.html', current_date=datetime.now())

# También asegúrate de tener esta ruta para contacto
@app.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('contact.html', current_date=datetime.now())

@app.route('/api/cookies/status')
def cookie_status():
    """Obtener estado actual de cookies"""
    settings = get_cookie_settings()
    return jsonify({
        'consent_given': settings.get('cookie_consent_given', False),
        'consent_date': settings.get('cookie_consent_date'),
        'settings': settings
    })

# -----------------------------
# RUTAS PROTEGIDAS DE HÁBITOS
# -----------------------------
@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    """Añadir un nuevo hábito a la base de datos"""
    if not validate_csrf_token():
        flash('Token de seguridad inválido', 'error')
        return redirect(url_for('index'))
    
    if habits_collection is None:
        flash('Error de conexión con la base de datos', 'error')
        return redirect(url_for('index'))
    
    habit_name = request.form.get('habit_name')
    habit_description = request.form.get('habit_description')
    
    if habit_name:
        try:
            habit = {
                'name': habit_name,
                'description': habit_description,
                'created_at': datetime.now(),
                'completed_dates': [],
                'user_id': session['user_id']
            }
            habits_collection.insert_one(habit)
            flash('¡Hábito agregado correctamente!', 'success')
        except Exception as e:
            print(f"ERROR en add_habit: {e}")
            flash('Error al agregar el hábito', 'error')
    else:
        flash('El nombre del hábito es requerido', 'error')
    
    return redirect(url_for('index'))

@app.route('/complete_habit/<habit_id>', methods=['POST'])
@login_required
def complete_habit(habit_id):
    """Marcar un hábito como completado para hoy"""
    if not validate_csrf_token():
        flash('Token de seguridad inválido', 'error')
        return redirect(url_for('index'))
    
    if habits_collection is None:
        flash('Error de conexión con la base de datos', 'error')
        return redirect(url_for('index'))
    
    try:
        # Verificar que el hábito pertenece al usuario
        habit = habits_collection.find_one({
            '_id': ObjectId(habit_id),
            'user_id': session['user_id']
        })
        
        if not habit:
            flash('Hábito no encontrado', 'error')
            return redirect(url_for('index'))
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Verificar si ya está completado hoy
        completed_dates = habit.get('completed_dates', [])
        if today in completed_dates:
            flash('Este hábito ya fue completado hoy', 'info')
            return redirect(url_for('index'))
        
        # Actualizar el hábito
        result = habits_collection.update_one(
            {'_id': ObjectId(habit_id), 'user_id': session['user_id']},
            {'$push': {'completed_dates': today}}
        )
        
        if result.modified_count > 0:
            flash('¡Hábito completado! ✅', 'success')
        else:
            flash('No se pudo completar el hábito', 'error')
            
    except Exception as e:
        print(f"ERROR en complete_habit: {e}")
        flash('Error al completar el hábito', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_habit/<habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Eliminar un hábito de la base de datos"""
    if not validate_csrf_token():
        flash('Token de seguridad inválido', 'error')
        return redirect(url_for('index'))
    
    if habits_collection is None:
        flash('Error de conexión con la base de datos', 'error')
        return redirect(url_for('index'))
    
    try:
        # Verificar que el hábito pertenece al usuario antes de eliminar
        result = habits_collection.delete_one({
            '_id': ObjectId(habit_id),
            'user_id': session['user_id']
        })
        
        if result.deleted_count > 0:
            flash('Hábito eliminado correctamente', 'success')
        else:
            flash('Hábito no encontrado', 'error')
    except Exception as e:
        print(f"ERROR en delete_habit: {e}")
        flash('Error al eliminar el hábito', 'error')
    
    return redirect(url_for('index'))

@app.route('/edit_habit/<habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Editar un hábito existente"""
    if habits_collection is None:
        flash('Error de conexión con la base de datos', 'error')
        return redirect(url_for('index'))
    
    try:
        # Verificar que el hábito pertenece al usuario
        habit = habits_collection.find_one({
            '_id': ObjectId(habit_id),
            'user_id': session['user_id']
        })
        
        if not habit:
            flash('Hábito no encontrado', 'error')
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            if not validate_csrf_token():
                flash('Token de seguridad inválido', 'error')
                return redirect(url_for('edit_habit', habit_id=habit_id))
            
            habit_name = request.form.get('habit_name')
            habit_description = request.form.get('habit_description')
            
            if habit_name:
                # Actualizar el hábito
                result = habits_collection.update_one(
                    {'_id': ObjectId(habit_id), 'user_id': session['user_id']},
                    {'$set': {
                        'name': habit_name,
                        'description': habit_description
                    }}
                )
                
                if result.modified_count > 0:
                    flash('¡Hábito actualizado correctamente!', 'success')
                else:
                    flash('No se realizaron cambios en el hábito', 'info')
                return redirect(url_for('index'))
            else:
                flash('El nombre del hábito es requerido', 'error')
        
        # Si es GET, mostrar el formulario de edición
        return render_template('edit_habit.html', habit=habit)
        
    except Exception as e:
        print(f"ERROR en edit_habit: {e}")
        flash('Error al cargar el hábito para edición', 'error')
        return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario"""
    try:
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        habit_count = habits_collection.count_documents({'user_id': session['user_id']})
        
        # Calcular hábitos completados hoy
        today = datetime.now().strftime('%Y-%m-%d')
        completed_today = habits_collection.count_documents({
            'user_id': session['user_id'],
            'completed_dates': today
        })
        
    except Exception as e:
        user = None
        habit_count = 0
        completed_today = 0
        print(f"ERROR en profile: {e}")
        flash('Error al cargar el perfil', 'error')
    
    return render_template('profile.html', 
                        user=user, 
                        habit_count=habit_count, 
                        completed_today=completed_today)

# -----------------------------
# RUTAS PARA APRENDIZAJE Y ANALÍTICAS
# -----------------------------
@app.route('/api/analytics/behavior', methods=['POST'])
@login_required
def track_user_behavior():
    """Trackear comportamiento del usuario para aprendizaje"""
    try:
        if not validate_csrf_token():
            return jsonify({'error': 'Token CSRF inválido'}), 403
        
        data = request.get_json()
        
        # Verificar consentimiento de analytics
        cookie_settings = get_cookie_settings()
        if not cookie_settings.get('analytics_cookies', False):
            return jsonify({'error': 'Analytics no permitido'}), 403
        
        # Guardar datos de comportamiento
        behavior_data = {
            'user_id': session['user_id'],
            'event_type': data.get('event_type'),
            'event_data': data.get('event_data', {}),
            'timestamp': datetime.now(),
            'anonymous': cookie_settings.get('anonymous_data', True)
        }
        
        # Aquí podrías guardar en una colección de analytics
        # Por ahora solo lo registramos
        print(f"Behavior tracked: {behavior_data}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/recommendations')
@login_required
def get_recommendations():
    """Obtener recomendaciones basadas en aprendizaje"""
    try:
        # Verificar consentimiento de cookies funcionales
        cookie_settings = get_cookie_settings()
        if not cookie_settings.get('functional_cookies', False):
            return jsonify({'recommendations': []})
        
        # Obtener hábitos del usuario
        habits = list(habits_collection.find(
            {'user_id': session['user_id']}
        ))
        
        # Generar recomendaciones simples basadas en hábitos
        recommendations = []
        
        # Recomendación 1: Si no tiene hábitos de ejercicio
        exercise_habits = [h for h in habits if 'ejercicio' in h['name'].lower() or 
                          'correr' in h['name'].lower() or 
                          'gimnasio' in h['name'].lower()]
        
        if not exercise_habits:
            recommendations.append({
                'type': 'exercise',
                'message': '¿Has considerado agregar un hábito de ejercicio?',
                'suggestion': 'Ejercicio diario',
                'priority': 'high'
            })
        
        # Recomendación 2: Si no tiene hábitos de lectura
        reading_habits = [h for h in habits if 'leer' in h['name'].lower() or 
                         'lectura' in h['name'].lower()]
        
        if not reading_habits:
            recommendations.append({
                'type': 'reading',
                'message': 'La lectura es un excelente hábito para desarrollar',
                'suggestion': 'Leer 30 minutos al día',
                'priority': 'medium'
            })
        
        # Recomendación 3: Basada en completado
        completion_rate = 0
        if habits:
            today = datetime.now().strftime('%Y-%m-%d')
            completed_today = sum(1 for h in habits if today in h.get('completed_dates', []))
            completion_rate = (completed_today / len(habits)) * 100
            
            if completion_rate < 50:
                recommendations.append({
                    'type': 'motivation',
                    'message': f'Tu tasa de completado hoy es del {completion_rate:.1f}%',
                    'suggestion': '¡Vamos, puedes completar más hábitos!',
                    'priority': 'high'
                })
            elif completion_rate == 100:
                recommendations.append({
                    'type': 'congratulations',
                    'message': '¡Felicidades! Has completado todos tus hábitos hoy',
                    'suggestion': 'Mantén esta racha',
                    'priority': 'low'
                })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'completion_rate': completion_rate,
            'total_habits': len(habits)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -----------------------------
# MIDDLEWARE DE SEGURIDAD
# -----------------------------
@app.after_request
def add_security_headers(response):
    """Añadir headers de seguridad a todas las respuestas"""
    # Content Security Policy
    csp = "default-src 'self'; " \
          "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " \
          "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; " \
          "font-src 'self' data: https://cdn.jsdelivr.net; " \
          "img-src 'self' data:; " \
          "connect-src 'self'"
    
    response.headers['Content-Security-Policy'] = csp
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Headers específicos para cookies
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    
    return response

# -----------------------------
# RUN
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # En producción no usar debug=True
    app.run(host='0.0.0.0', port=port, debug=False)