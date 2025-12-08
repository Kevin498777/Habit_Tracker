# HabitTracker - Sistema de Seguimiento de Hábitos

## Descripción
Aplicación web para registro y seguimiento de hábitos diarios. Permite crear hábitos, marcar cumplimiento y visualizar estadísticas de progreso.

## Características
- Registro y autenticación de usuarios
- Creación y gestión de hábitos
- Estadísticas de progreso diario/semanal
- Marcado de hábitos completados
- Diseño responsive e intuitivo
- Seguridad robusta con autenticación

## Tecnologías
- Backend: Python + Flask
- Base de Datos: MongoDB Atlas
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Autenticación: Sessions + Werkzeug Security

## Prerrequisitos
- Python 3.8+
- Cuenta MongoDB Atlas
- Git

## Instalación

1. Clonar repositorio:
git clone https://github.com/tuusuario/habit-tracker.git
cd habit-tracker

2. Crear entorno virtual:
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

3. Instalar dependencias:
pip install -r requirements.txt

4. Configurar archivo .env:
SECRET_KEY=tu_clave_secreta_muy_segura_aqui
MONGODB_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/habit_tracker
FLASK_DEBUG=False
FLASK_ENV=production

5. Ejecutar aplicación:
python app.py

La aplicación estará en: http://localhost:5001

## Estructura del Proyecto
habit_tracker/
├── app.py                 # Aplicación principal
├── config.py             # Configuración
├── requirements.txt      # Dependencias
├── .env                 # Variables de entorno
├── static/
│   ├── css/style.css    # Estilos
│   └── js/app.js        # JavaScript
└── templates/
    ├── base.html        # Template base
    ├── index.html       # Página principal
    ├── login.html       # Login
    ├── register.html    # Registro
    ├── profile.html     # Perfil
    └── edit_habit.html  # Edición hábitos

## Uso
1. Registrar nueva cuenta
2. Iniciar sesión
3. Agregar hábitos diarios
4. Marcar como completados
5. Ver progreso en estadísticas

## Funcionalidades
- Crear, editar, eliminar hábitos
- Marcar completado diario
- Ver progreso y estadísticas
- Gestión de perfil de usuario
- Historial de hábitos completados

## Seguridad
- Autenticación con sesiones Flask
- Hash de contraseñas con Werkzeug
- Validación de ownership
- Protección contra inyecciones
- Variables sensibles en .env

## Soporte
Para problemas o consultas:
- Abrir issue en el repositorio
- Contactar al desarrollador

¡Comienza a construir mejores hábitos hoy mismo!