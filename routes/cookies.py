# routes/cookies.py — Blueprint de gestión de cookies y consentimiento
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session, jsonify
)

from config.database import get_users_collection
from services.cookies import (
    get_cookie_settings, save_cookie_settings, build_settings_from_form
)
from services.security import login_required, validate_csrf_token

cookies_bp = Blueprint('cookies', __name__)


@cookies_bp.route('/cookies-policy')
def cookies_policy():
    return render_template('cookies_policy.html', current_date=datetime.now())


@cookies_bp.route('/cookie-settings', methods=['GET', 'POST'])
def cookie_settings():
    """Página de configuración granular de cookies."""
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Token de seguridad inválido.', 'error')
            return redirect(url_for('cookies.cookie_settings'))

        settings = build_settings_from_form(request.form)
        save_cookie_settings(settings, get_users_collection())
        flash('Configuración de cookies guardada correctamente.', 'success')
        return redirect(url_for('cookies.cookie_settings'))

    return render_template(
        'cookie_settings.html',
        cookie_settings=get_cookie_settings()
    )


@cookies_bp.route('/save-cookie-settings', methods=['POST'])
def save_cookie_settings_route():
    """Endpoint AJAX para guardar configuración de cookies desde JavaScript."""
    if not validate_csrf_token():
        return jsonify({'error': 'Token CSRF inválido.'}), 403

    data = request.get_json(silent=True) or {}
    required = ['preference_cookies', 'analytics_cookies', 'functional_cookies', 'data_retention']

    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({'error': f'Campos faltantes: {", ".join(missing)}'}), 400

    settings = {
        'essential_cookies':    True,
        'preference_cookies':   data['preference_cookies'],
        'analytics_cookies':    data['analytics_cookies'],
        'functional_cookies':   data['functional_cookies'],
        'third_party_cookies':  data.get('third_party_cookies', False),
        'anonymous_data':       data.get('anonymous_data', True),
        'same_site_cookies':    data.get('same_site_cookies', True),
        'data_retention':       data['data_retention'],
        'performance_cookies':  data.get('performance_cookies', True),
        'cookie_consent_given': True,
        'cookie_consent_date':  datetime.now(),
    }

    save_cookie_settings(settings, get_users_collection())
    return jsonify({'success': True, 'message': 'Configuración guardada.'})


@cookies_bp.route('/api/cookies/consent', methods=['POST'])
def record_cookie_consent():
    """Registra el tipo de consentimiento elegido en el banner (all / essential / custom)."""
    if not validate_csrf_token():
        return jsonify({'error': 'Token CSRF inválido.'}), 403

    data         = request.get_json(silent=True) or {}
    consent_type = data.get('type', 'all')
    settings     = get_cookie_settings()

    if consent_type == 'all':
        settings.update({
            'preference_cookies':   True,
            'analytics_cookies':    True,
            'functional_cookies':   True,
            'cookie_consent_given': True,
            'cookie_consent_date':  datetime.now(),
        })
    elif consent_type == 'essential':
        settings.update({
            'preference_cookies':   False,
            'analytics_cookies':    False,
            'functional_cookies':   False,
            'cookie_consent_given': True,
            'cookie_consent_date':  datetime.now(),
        })

    save_cookie_settings(settings, get_users_collection())
    return jsonify({'success': True, 'consent_date': datetime.now().isoformat()})


@cookies_bp.route('/api/cookies/clear', methods=['POST'])
@login_required
def clear_cookies():
    """Elimina toda la configuración de cookies del usuario."""
    if not validate_csrf_token():
        return jsonify({'error': 'Token CSRF inválido.'}), 403

    session.pop('cookie_settings', None)

    try:
        from bson import ObjectId
        get_users_collection().update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$unset': {'cookie_settings': ''}}
        )
    except Exception as e:
        print(f"Error eliminando cookie_settings de DB: {e}")

    response = jsonify({'success': True, 'message': 'Cookies eliminadas correctamente.'})
    response.set_cookie('user_preferences',  '', expires=0)
    response.set_cookie('analytics_consent', '', expires=0)
    return response


@cookies_bp.route('/api/cookies/status')
def cookie_status():
    """Devuelve el estado actual de las cookies del usuario (para uso de JS)."""
    settings = get_cookie_settings()
    return jsonify({
        'consent_given': settings.get('cookie_consent_given', False),
        'consent_date':  str(settings.get('cookie_consent_date', '')),
        'settings':      settings,
    })