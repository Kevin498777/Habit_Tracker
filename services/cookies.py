# services/cookies.py — Lógica de negocio para gestión de cookies
import json
from datetime import datetime

from flask import session, request
#from bson import ObjectId


# ── Configuración de cookies ───────────────────────────────────────────────────

class CookieConfig:
    DEFAULT_SETTINGS = {
        'essential_cookies':     True,
        'preference_cookies':    True,
        'analytics_cookies':     True,
        'functional_cookies':    True,
        'third_party_cookies':   False,
        'anonymous_data':        True,
        'same_site_cookies':     True,
        'data_retention':        '730',
        'performance_cookies':   True,
        'cookie_consent_given':  False,
        'cookie_consent_date':   None,
        'last_updated':          None,
    }

    EXPIRATION = {
        'session':       0,
        'short_term':    86_400,       # 1 día
        'medium_term':   2_592_000,    # 30 días
        'long_term':     31_536_000,   # 1 año
        'extended_term': 63_072_000,   # 2 años
    }


# ── Funciones de acceso ────────────────────────────────────────────────────────

def get_cookie_settings() -> dict:
    """
    Devuelve la configuración de cookies del usuario en este orden de prioridad:
    1. Sesión Flask (más rápido, ya cargado)
    2. Cookie del navegador 'user_preferences'
    3. Valores por defecto de CookieConfig
    """
    if 'cookie_settings' in session:
        return session['cookie_settings']

    raw = request.cookies.get('user_preferences')
    if raw:
        try:
            settings = json.loads(raw)
            session['cookie_settings'] = settings
            return settings
        except (json.JSONDecodeError, ValueError):
            pass

    return CookieConfig.DEFAULT_SETTINGS.copy()


def save_cookie_settings(settings: dict, users_collection=None) -> dict:
    """
    Persiste la configuración de cookies:
    - Siempre en la sesión Flask.
    - Si el usuario está autenticado, también en Firestore.
    """
    settings['last_updated'] = datetime.now().isoformat()
    session['cookie_settings'] = settings

    if 'user_id' in session and users_collection is not None:
        try:
            users_collection.document(session['user_id']).update({
                'cookie_settings': settings
            })
        except Exception as e:
            print(f"Error guardando configuración de cookies en DB: {e}")

    return settings


def build_settings_from_form(form_data: dict) -> dict:
    """Construye el dict de configuración a partir de los datos de un formulario POST."""
    return {
        'essential_cookies':    True,   # Siempre activas
        'preference_cookies':   form_data.get('preference_cookies') == 'on',
        'analytics_cookies':    form_data.get('analytics_cookies') == 'on',
        'functional_cookies':   form_data.get('functional_cookies') == 'on',
        'third_party_cookies':  form_data.get('third_party_cookies') == 'on',
        'anonymous_data':       form_data.get('anonymous_data') == 'on',
        'same_site_cookies':    form_data.get('same_site_cookies') == 'on',
        'data_retention':       form_data.get('data_retention', '730'),
        'performance_cookies':  form_data.get('performance_cookies') == 'on',
        'cookie_consent_given': True,
        'cookie_consent_date':  datetime.now(),
    }