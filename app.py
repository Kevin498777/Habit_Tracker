# app.py
import os
import re
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, Response
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
def count_requests():
    # Contador de requests por método y endpoint
    try:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path
        ).inc()
    except Exception:
        pass

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
            user = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'created_at': datetime.now(),
                'last_login': None
            }
            
            result = users_collection.insert_one(user)
            
            # Iniciar sesión automáticamente
            session['user_id'] = str(result.inserted_id)
            session['username'] = username
            session['email'] = email
            
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'error')
            return render_template('login.html')
        
        try:
            # Buscar usuario por username o email
            user = users_collection.find_one({
                '$or': [
                    {'username': username},
                    {'email': username}
                ]
            })
        except Exception as e:
            user = None
            print(f"ERROR en login al buscar usuario: {e}")
        
        if user and check_password_hash(user['password'], password):
            try:
                # Actualizar último login
                users_collection.update_one(
                    {'_id': user['_id']},
                    {'$set': {'last_login': datetime.now()}}
                )
            except Exception as e:
                print(f"ERROR actualizando last_login: {e}")
            
            # Establecer sesión
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['email'] = user['email']
            
            flash(f'¡Bienvenido de nuevo {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('login'))

# -----------------------------
# RUTAS PROTEGIDAS DE HÁBITOS
# -----------------------------
@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    """Añadir un nuevo hábito a la base de datos"""
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
# RUN
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # En producción no usar debug=True
    app.run(host='0.0.0.0', port=port, debug=False)
