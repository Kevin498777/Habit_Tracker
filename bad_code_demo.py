"""
ARCHIVO DE DEMOSTRACIÓN - VULNERABILIDADES INTENCIONALES
Este archivo es solo para mostrar cómo el pipeline detecta problemas de seguridad.
"""

# VULNERABILIDAD 1: Contraseña hardcodeada
# Bandit detectará: B105 (hardcoded_password_string)
database_password = "SuperSecret123!"
api_key = "DEMO_KEY_NO_ES_REAL"

# VULNERABILIDAD 2: Posible SQL Injection
# Bandit detectará: B608 (hardcoded_sql_expressions)
def get_user_data(username):
    # MAL: Concatenación directa de entrada de usuario
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return query

# VULNERABILIDAD 3: Uso de MD5 (hash inseguro)
import hashlib
def insecure_hash(password):
    # MAL: MD5 es considerado inseguro
    return hashlib.md5(password.encode()).hexdigest()

# VULNERABILIDAD 4: Debug habilitado en "producción"
DEBUG = True  # Bandit detectará: B104 (hardcoded_bind_all_interfaces)
HOST = "0.0.0.0"  # Escucha en todas las interfaces

print("Este archivo solo es para demostración de seguridad")
