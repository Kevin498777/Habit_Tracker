# routes/habits.py — Blueprint de hábitos adaptado a Firestore
from datetime import datetime, timedelta

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