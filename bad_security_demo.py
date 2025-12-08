#  ARCHIVO DE DEMO - HACER FALLAR PIPELINE
# Este archivo tiene vulnerabilidades intencionales

# 1. CONTRASEÑA HARCODEADA (Bandit la detectará SEGURO)
DB_PASSWORD = "admin123"

# 2. INYECCIÓN SQL (Otro patrón que Bandit detecta)
def get_data(user):
    return f"SELECT * FROM users WHERE name = '{user}'"

# 3. SHELL INJECTION (Vulnerabilidad de alta severidad)
import os
def run_cmd(cmd):
    os.system(f"echo {cmd}")  # Peligroso!

# 4. DEBUG HABILITADO
DEBUG = True

print("Demo: Pipeline debería fallar por estas vulnerabilidades")