# routes/auth.py — Blueprint de autenticación (registro, login, logout)
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash

from config.database import get_users_collection
from services.cookies import CookieConfig
from services.security import is_valid_email, validate_csrf_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios."""
    if 'user_id' in session:
        return redirect(url_for('habits.index'))

    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido.', 'error')
            return render_template('register.html')

        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # ── Validaciones ──────────────────────────────────────────────────────
        if not all([username, email, password, confirm_password]):
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('register.html')

        if not is_valid_email(email):
            flash('Por favor ingresa un email válido.', 'error')
            return render_template('register.html')

        users = get_users_collection()

        try:
            if users.find_one({'$or': [{'username': username}, {'email': email}]}):
                flash('El nombre de usuario o email ya están en uso.', 'error')
                return render_template('register.html')

            cookie_settings = CookieConfig.DEFAULT_SETTINGS.copy()
            cookie_settings['cookie_consent_date'] = datetime.now()

            user = {
                'username':        username,
                'email':           email,
                'password':        generate_password_hash(password),
                'created_at':      datetime.now(),
                'last_login':      None,
                'cookie_settings': cookie_settings,
            }
            result = users.insert_one(user)

            session['user_id']         = str(result.inserted_id)
            session['username']        = username
            session['email']           = email
            session['cookie_settings'] = cookie_settings

            flash(f'¡Bienvenido {username}! Tu cuenta fue creada exitosamente.', 'success')
            return redirect(url_for('habits.index'))

        except Exception as e:
            print(f"ERROR en register: {e}")
            flash('Error al crear la cuenta.', 'error')

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión."""
    if 'user_id' in session:
        return redirect(url_for('habits.index'))

    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido.', 'error')
            return render_template('login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Por favor completa todos los campos.', 'error')
            return render_template('login.html')

        try:
            users = get_users_collection()
            user  = users.find_one({
                '$or': [{'username': username}, {'email': username}]
            })

            if user and check_password_hash(user['password'], password):
                # Actualizar último login (no-crítico)
                try:
                    users.update_one(
                        {'_id': user['_id']},
                        {'$set': {'last_login': datetime.now()}}
                    )
                except Exception:
                    pass

                session['user_id']  = str(user['_id'])
                session['username'] = user['username']
                session['email']    = user['email']
                session['cookie_settings'] = user.get(
                    'cookie_settings',
                    CookieConfig.DEFAULT_SETTINGS.copy()
                )

                flash(f'¡Bienvenido de nuevo, {user["username"]}!', 'success')
                return redirect(url_for('habits.index'))

            flash('Usuario o contraseña incorrectos.', 'error')

        except Exception as e:
            print(f"ERROR en login: {e}")
            flash('Error al procesar el inicio de sesión. Intenta nuevamente.', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Cierre de sesión."""
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))