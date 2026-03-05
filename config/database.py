# config/database.py — Conexión y acceso a Firebase Firestore
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Variable global del cliente Firestore
_db = None


def init_db(app):
    """Inicializa Firebase Admin SDK al arrancar la app."""
    global _db

    cred_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'firebase-credentials.json'
    )

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        print("OK — Conectado a Firebase Firestore exitosamente.")
    except Exception as e:
        print(f"ERROR — No se pudo conectar a Firestore: {e}")
        _db = None


def get_db():
    """Devuelve el cliente de Firestore."""
    return _db


def get_users_collection():
    """Devuelve referencia a la colección 'users'."""
    return _db.collection('users') if _db else None


def get_habits_collection():
    """Devuelve referencia a la colección 'habits'."""
    return _db.collection('habits') if _db else None