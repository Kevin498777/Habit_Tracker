# app.py
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave-secreta-predeterminada')

# Configuración de MongoDB
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    # Verificar conexión
    client.admin.command('ping')
    print("OK - Conectado a MongoDB exitosamente!")
    
    db = client['habit_tracker']
    habits_collection = db['habits']
    users_collection = db['users']
    
except Exception as e:
    print(f"ERROR - Conectando a MongoDB: {e}")
    habits_collection = None
    users_collection = None

@app.route('/')
def index():
    """Página principal que muestra la lista de hábitos"""
    try:
        if habits_collection is not None:
            habits = list(habits_collection.find().sort('created_at', -1))
            # Calcular completados hoy
            today = datetime.now().strftime('%Y-%m-%d')
            today_completed = sum(1 for habit in habits if today in habit.get('completed_dates', []))
        else:
            habits = []
            today_completed = 0
            flash('Error de conexion con la base de datos', 'error')
    except Exception as e:
        habits = []
        today_completed = 0
        flash('Error al cargar los habitos', 'error')
    
    return render_template('index.html', habits=habits, today_completed=today_completed)

@app.route('/add_habit', methods=['POST'])
def add_habit():
    """Añadir un nuevo hábito a la base de datos"""
    if habits_collection is None:
        flash('Error de conexion con la base de datos', 'error')
        return redirect(url_for('index'))
    
    habit_name = request.form.get('habit_name')
    habit_description = request.form.get('habit_description')
    
    if habit_name:
        habit = {
            'name': habit_name,
            'description': habit_description,
            'created_at': datetime.now(),
            'completed_dates': [],
            'user_id': session.get('user_id', 'anonymous')
        }
        habits_collection.insert_one(habit)
        flash('Habito agregado correctamente!', 'success')
    else:
        flash('El nombre del habito es requerido', 'error')
    
    return redirect(url_for('index'))

@app.route('/complete_habit/<habit_id>', methods=['POST'])
def complete_habit(habit_id):
    """Marcar un hábito como completado para hoy"""
    if habits_collection is None:
        flash('Error de conexion con la base de datos', 'error')
        return redirect(url_for('index'))
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        result = habits_collection.update_one(
            {'_id': ObjectId(habit_id)},
            {'$addToSet': {'completed_dates': today}}
        )
        
        if result.modified_count > 0:
            flash('Habito completado!', 'success')
        else:
            flash('El habito ya estaba completado hoy', 'info')
    except Exception as e:
        flash('Error al completar el habito', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete_habit/<habit_id>', methods=['POST'])
def delete_habit(habit_id):
    """Eliminar un hábito de la base de datos"""
    if habits_collection is None:
        flash('Error de conexion con la base de datos', 'error')
        return redirect(url_for('index'))
    
    try:
        result = habits_collection.delete_one({'_id': ObjectId(habit_id)})
        if result.deleted_count > 0:
            flash('Habito eliminado correctamente', 'success')
        else:
            flash('Habito no encontrado', 'error')
    except Exception as e:
        flash('Error al eliminar el habito', 'error')
    
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('Funcionalidad de login en desarrollo', 'info')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Funcionalidad de registro en desarrollo', 'info')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesion', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', True), host='127.0.0.1', port=5001)