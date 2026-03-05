# app.py — Punto de entrada principal
from flask import Flask
from config.settings import Config
from config.database import init_db
from config.metrics import init_metrics
from routes.auth import auth_bp
from routes.habits import habits_bp
from routes.cookies import cookies_bp
from routes.pages import pages_bp
from routes.api import api_bp
from services.security import register_security_middleware


def create_app():
    """Application Factory — patrón recomendado por Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar base de datos
    init_db(app)

    # Inicializar métricas Prometheus
    init_metrics(app)

    # Registrar middleware de seguridad (headers HTTP + CSRF logging)
    register_security_middleware(app)

    # Registrar Blueprints (módulos de rutas)
    app.register_blueprint(auth_bp)
    app.register_blueprint(habits_bp)
    app.register_blueprint(cookies_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)