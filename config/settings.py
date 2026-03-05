# config/settings.py — Configuración centralizada de la aplicación
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Seguridad ──────────────────────────────────────────────────────────────
    # NUNCA dejar un valor por defecto en producción.
    # Si SECRET_KEY no está en .env, la app lanza un error en vez de
    # continuar con una clave insegura.
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY no está definida. "
            "Agrégala a tu archivo .env antes de iniciar la aplicación."
        )

    # ── Base de datos ──────────────────────────────────────────────────────────
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb://localhost:27017/habit_tracker'
    )

    # ── Entorno ────────────────────────────────────────────────────────────────
    FLASK_ENV  = os.getenv('FLASK_ENV', 'production')
    DEBUG      = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # ── Sesión ─────────────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = 'Lax'
    SESSION_COOKIE_SECURE    = not DEBUG   # True en producción (HTTPS)