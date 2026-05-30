# routes/habits.py — Blueprint de hábitos adaptado a Firestore
import calendar as cal
from datetime import datetime, timedelta, date

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)

from config.database import get_habits_collection, get_users_collection
from services.security import login_required, validate_csrf_token

habits_bp = Blueprint('habits', __name__)


def _get_user_habits(user_id: str) -> list:
    """Obtiene todos los hábitos del usuario ordenados por fecha."""
    docs = (
        get_habits_collection()
        .where('user_id', '==', user_id)
        .stream()
    )
    habits = []
    for doc in docs:
        data = doc.to_dict()
        data['_id'] = doc.id

        # Convertir created_at de string a datetime para el template
        if isinstance(data.get('created_at'), str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = datetime.now()

        habits.append(data)

    habits.sort(key=lambda h: h.get('created_at', datetime.now()), reverse=True)
    return habits


@habits_bp.route('/')
@login_required
def index():
    """Dashboard principal con listado y estadísticas de hábitos."""
    habits           = []
    today_completed  = 0
    total_habits     = 0
    completion_rate  = 0.0
    week_completions = 0
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        habits       = _get_user_habits(session['user_id'])
        total_habits = len(habits)

        today_completed = sum(
            1 for h in habits if today in h.get('completed_dates', [])
        )

        if total_habits > 0:
            completion_rate = round((today_completed / total_habits) * 100, 1)

        week_dates = [
            (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(7)
        ]
        week_completions = sum(
            1 for h in habits
            if any(d in week_dates for d in h.get('completed_dates', []))
        )

    except Exception as e:
        print(f"ERROR en index: {e}")
        flash('Error al cargar los hábitos.', 'error')

    return render_template(
        'index.html',
        habits=habits,
        today=today,
        today_completed=today_completed,
        total_habits=total_habits,
        completion_rate=completion_rate,
        week_completions=week_completions,
    )


@habits_bp.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    """Crea un nuevo hábito."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    habit_name        = request.form.get('habit_name', '').strip()
    habit_description = request.form.get('habit_description', '').strip()

    if not habit_name:
        flash('El nombre del hábito es requerido.', 'error')
        return redirect(url_for('habits.index'))

    try:
        get_habits_collection().add({
            'name':            habit_name,
            'description':     habit_description,
            'created_at':      datetime.now().isoformat(),
            'completed_dates': [],
            'user_id':         session['user_id'],
        })
        flash('¡Hábito agregado correctamente!', 'success')
    except Exception as e:
        print(f"ERROR en add_habit: {e}")
        flash('Error al agregar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/complete_habit/<habit_id>', methods=['POST'])
@login_required
def complete_habit(habit_id):
    """Marca un hábito como completado para hoy."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    today = datetime.now().strftime('%Y-%m-%d')

    try:
        habits_col = get_habits_collection()
        doc_ref    = habits_col.document(habit_id)
        doc        = doc_ref.get()

        if not doc.exists or doc.to_dict().get('user_id') != session['user_id']:
            flash('Hábito no encontrado.', 'error')
            return redirect(url_for('habits.index'))

        habit = doc.to_dict()
        completed_dates = habit.get('completed_dates', [])

        if today in completed_dates:
            flash('Este hábito ya fue completado hoy.', 'info')
            return redirect(url_for('habits.index'))

        completed_dates.append(today)
        doc_ref.update({'completed_dates': completed_dates})
        flash('¡Hábito completado! ✅', 'success')

    except Exception as e:
        print(f"ERROR en complete_habit: {e}")
        flash('Error al completar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/edit_habit/<habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Edita nombre y descripción de un hábito."""
    try:
        habits_col = get_habits_collection()
        doc_ref    = habits_col.document(habit_id)
        doc        = doc_ref.get()

        if not doc.exists or doc.to_dict().get('user_id') != session['user_id']:
            flash('Hábito no encontrado.', 'error')
            return redirect(url_for('habits.index'))

        habit = doc.to_dict()
        habit['_id'] = habit_id

        if request.method == 'POST':
            if not validate_csrf_token():
                flash('Token de seguridad inválido.', 'error')
                return render_template('edit_habit.html', habit=habit)

            habit_name        = request.form.get('habit_name', '').strip()
            habit_description = request.form.get('habit_description', '').strip()

            if not habit_name:
                flash('El nombre del hábito es requerido.', 'error')
                return render_template('edit_habit.html', habit=habit)

            doc_ref.update({'name': habit_name, 'description': habit_description})
            flash('¡Hábito actualizado!', 'success')
            return redirect(url_for('habits.index'))

    except Exception as e:
        print(f"ERROR en edit_habit: {e}")
        flash('Error al cargar el hábito.', 'error')
        return redirect(url_for('habits.index'))

    return render_template('edit_habit.html', habit=habit)


@habits_bp.route('/delete_habit/<habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Elimina un hábito."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    try:
        doc_ref = get_habits_collection().document(habit_id)
        doc     = doc_ref.get()

        if not doc.exists or doc.to_dict().get('user_id') != session['user_id']:
            flash('Hábito no encontrado.', 'error')
            return redirect(url_for('habits.index'))

        doc_ref.delete()
        flash('Hábito eliminado correctamente.', 'success')

    except Exception as e:
        print(f"ERROR en delete_habit: {e}")
        flash('Error al eliminar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario."""
    user            = None
    habit_count     = 0
    completed_today = 0
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        # Obtener datos del usuario
        doc = get_users_collection().document(session['user_id']).get()
        if doc.exists:
            user = doc.to_dict()
            user['_id'] = doc.id
            # Convertir created_at a datetime si es string
            if isinstance(user.get('created_at'), str):
                user['created_at'] = datetime.fromisoformat(user['created_at'])

        habits      = _get_user_habits(session['user_id'])
        habit_count = len(habits)
        completed_today = sum(
            1 for h in habits if today in h.get('completed_dates', [])
        )

    except Exception as e:
        print(f"ERROR en profile: {e}")
        flash('Error al cargar el perfil.', 'error')

    return render_template(
        'profile.html',
        user=user,
        habit_count=habit_count,
        completed_today=completed_today,
    )

@habits_bp.route('/calendario')
@login_required
def calendar_view():
    """
    Vista de calendario mensual con hábitos completados.
    Soporta vista global (todos los hábitos) y filtrada por hábito individual.

    Query params:
        - year: año a mostrar (default: año actual)
        - month: mes a mostrar (1-12, default: mes actual)
        - habit_id: ID del hábito a filtrar (opcional, vacío = todos)
    """
    today = date.today()

    # --- Parsear parámetros con validación ---
    try:
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
        if month < 1 or month > 12:
            raise ValueError
    except (ValueError, TypeError):
        year, month = today.year, today.month

    selected_habit_id = request.args.get('habit_id', '').strip() or None

    # --- Obtener hábitos del usuario (reutilizamos el helper que ya existe) ---
    user_habits = []
    habits_to_show = []
    month_stats = {'total_completions': 0, 'active_days': 0, 'best_streak': 0}
    calendar_days = []

    try:
        user_habits = _get_user_habits(session['user_id'])

        # Filtrar si se seleccionó un hábito específico
        if selected_habit_id:
            habits_to_show = [
                h for h in user_habits
                if str(h.get('_id')) == selected_habit_id
            ]
        else:
            habits_to_show = user_habits

        # --- Construir matriz del calendario ---
        cal.setfirstweekday(cal.MONDAY)
        month_calendar = cal.monthcalendar(year, month)

        days_with_activity = set()
        total_completions = 0

        for week in month_calendar:
            for day_num in week:
                if day_num == 0:
                    calendar_days.append({'empty': True})
                    continue

                day_date = date(year, month, day_num)
                day_str = day_date.strftime('%Y-%m-%d')  # mismo formato que usas en complete_habit

                # Contar hábitos completados ese día
                habits_completed_today = []
                for h in habits_to_show:
                    if day_str in h.get('completed_dates', []):
                        habits_completed_today.append(h.get('name', 'Sin nombre'))

                completed_count = len(habits_completed_today)
                total_count = len(habits_to_show)

                # Determinar nivel de completitud (para el color)
                if completed_count == 0:
                    completion_level = 'none'
                elif selected_habit_id:
                    completion_level = 'full'
                elif completed_count == total_count and total_count > 0:
                    completion_level = 'full'
                elif completed_count >= total_count / 2:
                    completion_level = 'partial'
                else:
                    completion_level = 'single'

                if habits_completed_today:
                    tooltip = '<strong>Completados:</strong><br>• ' + '<br>• '.join(habits_completed_today)
                    days_with_activity.add(day_str)
                    total_completions += completed_count
                else:
                    tooltip = ''

                calendar_days.append({
                    'empty': False,
                    'day': day_num,
                    'date': day_str,
                    'is_today': day_date == today,
                    'completed_count': completed_count,
                    'total_count': total_count,
                    'completion_level': completion_level,
                    'habits_completed': habits_completed_today,
                    'tooltip': tooltip,
                })

        # --- Mejor racha consecutiva del mes ---
        best_streak = _calculate_best_streak(days_with_activity, year, month)

        month_stats = {
            'total_completions': total_completions,
            'active_days': len(days_with_activity),
            'best_streak': best_streak,
        }

    except Exception as e:
        print(f"ERROR en calendar_view: {e}")
        flash('Error al cargar el calendario.', 'error')

    # --- Navegación entre meses ---
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    month_names_es = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]

    return render_template(
        'calendar.html',
        year=year,
        month=month,
        month_name=month_names_es[month],
        calendar_days=calendar_days,
        habits=user_habits,
        selected_habit_id=selected_habit_id,
        month_stats=month_stats,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


def _calculate_best_streak(active_days_set: set, year: int, month: int) -> int:
    """Calcula la racha máxima de días consecutivos con actividad en el mes."""
    if not active_days_set:
        return 0

    days_in_month = cal.monthrange(year, month)[1]
    best = 0
    current = 0

    for day in range(1, days_in_month + 1):
        day_str = date(year, month, day).strftime('%Y-%m-%d')
        if day_str in active_days_set:
            current += 1
            best = max(best, current)
        else:
            current = 0

    return best