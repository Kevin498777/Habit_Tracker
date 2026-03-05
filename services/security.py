# services/security.py — Middleware de seguridad y utilidades de validación
import re
import secrets
from functools import wraps

from flask import session, redirect, url_for, flash, request


# ── Middleware global ──────────────────────────────────────────────────────────

def register_security_middleware(app):
    """Registra el after_request que inyecta headers de seguridad en cada respuesta."""

    @app.after_request
    def add_security_headers(response):
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers['Content-Security-Policy']        = csp
        response.headers['X-Content-Type-Options']         = 'nosniff'
        response.headers['X-Frame-Options']                = 'DENY'
        response.headers['X-XSS-Protection']               = '1; mode=block'
        response.headers['Referrer-Policy']                = 'strict-origin-when-cross-origin'
        response.headers['Cross-Origin-Opener-Policy']     = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy']   = 'same-origin'
        return response


# ── Decoradores ────────────────────────────────────────────────────────────────

def login_required(f):
    """Protege rutas que requieren sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para acceder a esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Validaciones ───────────────────────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Valida formato de correo electrónico con expresión regular."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_csrf_token() -> bool:
    """
    Verifica que el token CSRF del formulario coincide con el de la cookie.
    Solo aplica en métodos que modifican estado (POST, PUT, DELETE, PATCH).
    """
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        form_token   = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        cookie_token = request.cookies.get('csrf_token')
        if not form_token or not cookie_token or form_token != cookie_token:
            return False
    return True


def generate_csrf_token() -> str:
    """Genera un token CSRF seguro de 32 bytes."""
    return secrets.token_urlsafe(32)