# app.py
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave-secreta-predeterminada')

# Configuración de MongoDB
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    client.admin.command('ping')
    print("OK - Conectado a MongoDB exitosamente!")
    
    db = client['habit_tracker']
    habits_collection = db['habits']
    users_collection = db['users']
    
except Exception as e:
    print(f"ERROR - Conectando a MongoDB: {e}")
    habits_collection = None
    users_collection = None

# Función para verificar si el usuario está logueado
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Función para validar email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@app.route('/')
def index():
    """Página principal que muestra la lista de hábitos"""
    # Si el usuario no está logueado, redirigir al login
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        if habits_collection is not None:
            # Solo obtener hábitos del usuario actual
            habits = list(habits_collection.find(
                {'user_id': session['user_id']}
            ).sort('created_at', -1))
            
            today = datetime.now().strftime('%Y-%m-%d')
            today_completed = sum(1 for habit in habits if today in habit.get('completed_dates', []))
        else:
            habits = []
            today_completed = 0
            flash('Error de conexión con la base de datos', 'error')
    except Exception as e:
        habits = []
        today_completed = 0
        flash('Error al cargar los hábitos', 'error')
    
    return render_template('index.html', habits=habits, today_completed=today_completed)

# RUTAS DE AUTENTICACIÓN
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios"""
    # Si ya está logueado, redirigir al index
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
        existing_user = users_collection.find_one({
            '$or': [
                {'username': username},
                {'email': email}
            ]
        })
        
        if existing_user:
            flash('El nombre de usuario o email ya están en uso', 'error')
            return render_template('register.html')
        
        # Crear nuevo usuario
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
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión de usuarios"""
    # Si ya está logueado, redirigir al index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Por favor completa todos los campos', 'error')
            return render_template('login.html')
        
        # Buscar usuario por username o email
        user = users_collection.find_one({
            '$or': [
                {'username': username},
                {'email': username}
            ]
        })
        
        if user and check_password_hash(user['password'], password):
            # Actualizar último login
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'last_login': datetime.now()}}
            )
            
            # Establecer sesión
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['email'] = user['email']
            
            flash(f'¡Bienvenido de nuevo {user["username"]}!', 'success')
            
            # Redirigir a la página que intentaba acceder o al index
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Has cerrado sesión exitosamente', 'info')
    return redirect(url_for('login'))

# RUTAS PROTEGIDAS DE HÁBITOS
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
        habit = {
            'name': habit_name,
            'description': habit_description,
            'created_at': datetime.now(),
            'completed_dates': [],
            'user_id': session['user_id']  # Asociar hábito al usuario
        }
        habits_collection.insert_one(habit)
        flash('¡Hábito agregado correctamente!', 'success')
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
        result = habits_collection.update_one(
            {'_id': ObjectId(habit_id), 'user_id': session['user_id']},
            {'$addToSet': {'completed_dates': today}}
        )
        
        if result.modified_count > 0:
            flash('¡Hábito completado!', 'success')
        else:
            flash('El hábito ya estaba completado hoy', 'info')
    except Exception as e:
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
        flash('Error al eliminar el hábito', 'error')
    
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
        flash('Error al cargar el perfil', 'error')
    
    return render_template('profile.html', 
                         user=user, 
                         habit_count=habit_count, 
                         completed_today=completed_today)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)