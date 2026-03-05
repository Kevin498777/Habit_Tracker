# config/database.py — Conexión y acceso a MongoDB
from flask import current_app, g
from pymongo import MongoClient


def get_db():
    """Devuelve la instancia de base de datos del contexto actual de Flask."""
    if 'db' not in g:
        client = MongoClient(current_app.config['MONGODB_URI'])
        g.db     = client['habit_tracker']
        g.client = client
    return g.db


def init_db(app):
    """Registra el teardown para cerrar la conexión al finalizar cada request."""

    @app.teardown_appcontext
    def close_db(error=None):
        client = g.pop('client', None)
        if client is not None:
            client.close()

    # Verificar conexión al arrancar
    with app.app_context():
        try:
            client = MongoClient(app.config['MONGODB_URI'])
            client.admin.command('ping')
            print("OK — Conectado a MongoDB exitosamente.")
            client.close()
        except Exception as e:
            print(f"ERROR — No se pudo conectar a MongoDB: {e}")


# ── Accesos rápidos a colecciones ──────────────────────────────────────────────
def get_users_collection():
    return get_db()['users']


def get_habits_collection():
    return get_db()['habits']