# routes/habits.py — Blueprint de gestión de hábitos (CRUD + dashboard)
from datetime import datetime, timedelta

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from bson import ObjectId

from config.database import get_habits_collection, get_users_collection
from services.security import login_required, validate_csrf_token

habits_bp = Blueprint('habits', __name__)


@habits_bp.route('/')
@login_required
def index():
    """Dashboard principal con listado y estadísticas de hábitos."""
    habits          = []
    today_completed = 0
    total_habits    = 0
    completion_rate = 0.0
    week_completions = 0
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        habits_col = get_habits_collection()
        habits = list(
            habits_col.find({'user_id': session['user_id']})
                      .sort('created_at', -1)
        )

        total_habits    = len(habits)
        today_completed = sum(1 for h in habits if today in h.get('completed_dates', []))

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
    """Crea un nuevo hábito para el usuario en sesión."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    habit_name        = request.form.get('habit_name', '').strip()
    habit_description = request.form.get('habit_description', '').strip()

    if not habit_name:
        flash('El nombre del hábito es requerido.', 'error')
        return redirect(url_for('habits.index'))

    try:
        get_habits_collection().insert_one({
            'name':             habit_name,
            'description':      habit_description,
            'created_at':       datetime.now(),
            'completed_dates':  [],
            'user_id':          session['user_id'],
        })
        flash('¡Hábito agregado correctamente!', 'success')
    except Exception as e:
        print(f"ERROR en add_habit: {e}")
        flash('Error al agregar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/complete_habit/<habit_id>', methods=['POST'])
@login_required
def complete_habit(habit_id):
    """Marca un hábito como completado para el día actual."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    today      = datetime.now().strftime('%Y-%m-%d')
    habits_col = get_habits_collection()

    try:
        habit = habits_col.find_one({
            '_id':     ObjectId(habit_id),
            'user_id': session['user_id'],
        })

        if not habit:
            flash('Hábito no encontrado.', 'error')
            return redirect(url_for('habits.index'))

        if today in habit.get('completed_dates', []):
            flash('Este hábito ya fue completado hoy.', 'info')
            return redirect(url_for('habits.index'))

        result = habits_col.update_one(
            {'_id': ObjectId(habit_id), 'user_id': session['user_id']},
            {'$push': {'completed_dates': today}}
        )
        if result.modified_count > 0:
            flash('¡Hábito completado! ✅', 'success')
        else:
            flash('No se pudo completar el hábito.', 'error')

    except Exception as e:
        print(f"ERROR en complete_habit: {e}")
        flash('Error al completar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/edit_habit/<habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Edita nombre y descripción de un hábito existente."""
    habits_col = get_habits_collection()

    try:
        habit = habits_col.find_one({
            '_id':     ObjectId(habit_id),
            'user_id': session['user_id'],
        })
        if not habit:
            flash('Hábito no encontrado.', 'error')
            return redirect(url_for('habits.index'))

        if request.method == 'POST':
            if not validate_csrf_token():
                flash('Token de seguridad inválido.', 'error')
                return redirect(url_for('habits.edit_habit', habit_id=habit_id))

            habit_name        = request.form.get('habit_name', '').strip()
            habit_description = request.form.get('habit_description', '').strip()

            if not habit_name:
                flash('El nombre del hábito es requerido.', 'error')
                return render_template('edit_habit.html', habit=habit)

            result = habits_col.update_one(
                {'_id': ObjectId(habit_id), 'user_id': session['user_id']},
                {'$set': {'name': habit_name, 'description': habit_description}}
            )
            flash(
                '¡Hábito actualizado!' if result.modified_count > 0
                else 'No se realizaron cambios.',
                'success' if result.modified_count > 0 else 'info'
            )
            return redirect(url_for('habits.index'))

    except Exception as e:
        print(f"ERROR en edit_habit: {e}")
        flash('Error al cargar el hábito para edición.', 'error')
        return redirect(url_for('habits.index'))

    return render_template('edit_habit.html', habit=habit)


@habits_bp.route('/delete_habit/<habit_id>', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Elimina permanentemente un hábito del usuario."""
    if not validate_csrf_token():
        flash('Token de seguridad inválido.', 'error')
        return redirect(url_for('habits.index'))

    try:
        result = get_habits_collection().delete_one({
            '_id':     ObjectId(habit_id),
            'user_id': session['user_id'],
        })
        flash(
            'Hábito eliminado correctamente.' if result.deleted_count > 0
            else 'Hábito no encontrado.',
            'success' if result.deleted_count > 0 else 'error'
        )
    except Exception as e:
        print(f"ERROR en delete_habit: {e}")
        flash('Error al eliminar el hábito.', 'error')

    return redirect(url_for('habits.index'))


@habits_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario con estadísticas."""
    user          = None
    habit_count   = 0
    completed_today = 0
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        user          = get_users_collection().find_one({'_id': ObjectId(session['user_id'])})
        habits_col    = get_habits_collection()
        habit_count   = habits_col.count_documents({'user_id': session['user_id']})
        completed_today = habits_col.count_documents({
            'user_id':          session['user_id'],
            'completed_dates':  today,
        })
    except Exception as e:
        print(f"ERROR en profile: {e}")
        flash('Error al cargar el perfil.', 'error')

    return render_template(
        'profile.html',
        user=user,
        habit_count=habit_count,
        completed_today=completed_today,
    )