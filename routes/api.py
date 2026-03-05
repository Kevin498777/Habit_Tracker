# routes/api.py — Blueprint de API interna (analíticas y recomendaciones)
from datetime import datetime

from flask import Blueprint, jsonify, request, session

from config.database import get_habits_collection
from services.cookies import get_cookie_settings
from services.security import login_required, validate_csrf_token

api_bp = Blueprint('api', __name__)


@api_bp.route('/analytics/behavior', methods=['POST'])
@login_required
def track_user_behavior():
    """Registra eventos de comportamiento del usuario (requiere consentimiento analítico)."""
    if not validate_csrf_token():
        return jsonify({'error': 'Token CSRF inválido.'}), 403

    cookie_settings = get_cookie_settings()
    if not cookie_settings.get('analytics_cookies', False):
        return jsonify({'error': 'Analytics no permitido por el usuario.'}), 403

    data = request.get_json(silent=True) or {}
    behavior_data = {
        'user_id':    session['user_id'],
        'event_type': data.get('event_type'),
        'event_data': data.get('event_data', {}),
        'timestamp':  datetime.now(),
        'anonymous':  cookie_settings.get('anonymous_data', True),
    }
    # TODO: persistir en colección 'analytics' de MongoDB
    print(f"Behavior tracked: {behavior_data}")

    return jsonify({'success': True})


@api_bp.route('/learning/recommendations')
@login_required
def get_recommendations():
    """
    Genera recomendaciones de hábitos basadas en los hábitos existentes del usuario.
    Requiere consentimiento de cookies funcionales.
    """
    cookie_settings = get_cookie_settings()
    if not cookie_settings.get('functional_cookies', False):
        return jsonify({'recommendations': []})

    try:
        habits = list(get_habits_collection().find({'user_id': session['user_id']}))
        recommendations = _build_recommendations(habits)
        today           = datetime.now().strftime('%Y-%m-%d')
        completed_today = sum(1 for h in habits if today in h.get('completed_dates', []))
        completion_rate = (completed_today / len(habits) * 100) if habits else 0

        return jsonify({
            'success':          True,
            'recommendations':  recommendations,
            'completion_rate':  completion_rate,
            'total_habits':     len(habits),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Helpers privados ───────────────────────────────────────────────────────────

def _build_recommendations(habits: list) -> list:
    """Genera lista de recomendaciones según los hábitos actuales del usuario."""
    names = [h['name'].lower() for h in habits]
    recs  = []

    # Ejercicio
    if not any(k in n for k in ('ejercicio', 'correr', 'gimnasio', 'deporte') for n in names):
        recs.append({
            'type':       'exercise',
            'message':    '¿Has considerado agregar un hábito de ejercicio?',
            'suggestion': 'Ejercicio diario — 30 min',
            'priority':   'high',
        })

    # Lectura
    if not any(k in n for k in ('leer', 'lectura', 'libro') for n in names):
        recs.append({
            'type':       'reading',
            'message':    'La lectura es un excelente hábito para desarrollar.',
            'suggestion': 'Leer 20 minutos al día',
            'priority':   'medium',
        })

    # Motivación basada en tasa de completado
    if habits:
        today           = datetime.now().strftime('%Y-%m-%d')
        completed_today = sum(1 for h in habits if today in h.get('completed_dates', []))
        rate            = (completed_today / len(habits)) * 100

        if rate == 100:
            recs.append({'type': 'congratulations', 'message': '¡Perfecto! Completaste todos tus hábitos hoy.', 'suggestion': 'Mantén la racha mañana.', 'priority': 'low'})
        elif rate < 50:
            recs.append({'type': 'motivation', 'message': f'Tu tasa de completado es del {rate:.0f}%.', 'suggestion': '¡Vamos, puedes completar más hábitos!', 'priority': 'high'})

    return recs