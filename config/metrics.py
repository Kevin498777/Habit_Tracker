# config/metrics.py — Métricas Prometheus centralizadas
from prometheus_client import Counter, Summary, generate_latest, CONTENT_TYPE_LATEST
from flask import Response, request

# ── Definición de métricas ─────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total de requests recibidos',
    ['method', 'endpoint']
)

EXCEPTIONS = Counter(
    'app_exceptions_total',
    'Total de excepciones no manejadas',
    ['endpoint', 'exception_type']
)

REQUEST_TIME = Summary(
    'app_request_processing_seconds',
    'Tiempo de procesamiento por request'
)


def init_metrics(app):
    """Registra los hooks de métricas y el endpoint /metrics en la app."""

    @app.before_request
    def count_request():
        try:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.path
            ).inc()
        except Exception:
            pass

    @app.errorhandler(Exception)
    def track_exception(e):
        # No contar errores HTTP esperados (404, 403, etc.) como excepciones
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e

        try:
            EXCEPTIONS.labels(
                endpoint=request.path,
                exception_type=type(e).__name__
            ).inc()
        except Exception:
            pass
        raise e

    @app.route('/metrics')
    def metrics():
        """Endpoint compatible con Prometheus scraping."""
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)