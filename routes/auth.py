# routes/auth.py — Blueprint de autenticación adaptado a Firestore
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


def _find_user_by_username_or_email(username: str):
    """Busca usuario por username o email en Firestore."""
    users = get_users_collection()

    # Buscar por username
    docs = users.where('username', '==', username).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['_id'] = doc.id
        return data

    # Buscar por email
    docs = users.where('email', '==', username).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['_id'] = doc.id
        return data

    return None


def _find_user_by_field(field: str, value: str):
    """Busca si ya existe un usuario con ese campo/valor."""
    users = get_users_collection()
    docs = users.where(field, '==', value).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None


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

        try:
            users = get_users_collection()

            # Verificar duplicados
            if _find_user_by_field('username', username):
                flash('El nombre de usuario ya está en uso.', 'error')
                return render_template('register.html')

            if _find_user_by_field('email', email):
                flash('El email ya está registrado.', 'error')
                return render_template('register.html')

            cookie_settings = CookieConfig.DEFAULT_SETTINGS.copy()
            cookie_settings['cookie_consent_date'] = datetime.now().isoformat()

            user_data = {
                'username':        username,
                'email':           email,
                'password':        generate_password_hash(password),
                'created_at':      datetime.now().isoformat(),
                'last_login':      None,
                'cookie_settings': cookie_settings,
            }

            # Firestore genera el ID automáticamente
            doc_ref = users.add(user_data)
            user_id = doc_ref[1].id

            session['user_id']         = user_id
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
            user = _find_user_by_username_or_email(username)

            if user and check_password_hash(user['password'], password):
                # Actualizar último login
                try:
                    get_users_collection().document(user['_id']).update({
                        'last_login': datetime.now().isoformat()
                    })
                except Exception:
                    pass

                session['user_id']  = user['_id']
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
            flash('Error al procesar el inicio de sesión.', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Cierre de sesión."""
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))