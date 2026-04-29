import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


def weekly_reset(app):
    """Elimina citas completadas/canceladas y todas las reseñas. Conserva citas pendientes."""
    with app.app_context():
        from app.models import Appointment, Review
        from datetime import date
        today = date.today().isoformat()
        deleted_appts = Appointment.query.filter(
            Appointment.status.in_(['Completado', 'Cancelado'])
        ).delete(synchronize_session=False)
        deleted_reviews = Review.query.delete(synchronize_session=False)
        db.session.commit()
        print(f"[Reset semanal] Citas eliminadas: {deleted_appts} | Reseñas eliminadas: {deleted_reviews}")


def complete_expired_appointments(app):
    """Completa automáticamente las citas que ya pasaron su hora + duración."""
    with app.app_context():
        from app.models import Appointment
        from datetime import datetime, date
        today = date.today().isoformat()
        
        # Obtener citas pendientes de hoy o en el pasado
        expired = Appointment.query.filter(
            Appointment.status == 'Pendiente',
            Appointment.date <= today
        ).all()
        
        completed_count = 0
        for appt in expired:
            # Calcular hora de finalización
            h, m = map(int, appt.time.split(':'))
            start_minutes = h * 60 + m
            duration = appt.duration_minutes or 60
            end_minutes = start_minutes + duration
            end_hour = end_minutes // 60
            end_min = end_minutes % 60
            end_time = f"{end_hour:02d}:{end_min:02d}"
            
            # Obtener hora actual
            now = datetime.now()
            current_time = f"{now.hour:02d}:{now.minute:02d}"
            
            # Si la hora actual es mayor o igual a la hora de finalización, completar
            if current_time >= end_time:
                appt.status = 'Completado'
                completed_count += 1
        
        if completed_count > 0:
            db.session.commit()
            print(f"[Completado automático] {completed_count} cita(s) completada(s)")


def _start_scheduler(app):
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    scheduler = BackgroundScheduler(daemon=True)
    
    # Completar citas vencidas cada 15 minutos
    scheduler.add_job(
        func=complete_expired_appointments,
        args=[app],
        trigger=IntervalTrigger(minutes=15),
        id='complete_expired',
        replace_existing=True
    )
    
    # Cada domingo a las 3:00 am
    scheduler.add_job(
        func=weekly_reset,
        args=[app],
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='weekly_reset',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler


def create_app():
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///barberking.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

    # ── Extensiones ────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request as req, jsonify as jfy
        if req.path.startswith('/api/') or req.is_json:
            return jfy({'success': False, 'message': 'No autorizado'}), 401
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    limiter.init_app(app)

    # ── Headers de seguridad ───────────────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=()'
        return response

    # ── Error handlers ─────────────────────────────────────────
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'success': False, 'message': 'Demasiadas solicitudes. Intenta más tarde.'}), 429

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'message': 'Recurso no encontrado'}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

    # ── Blueprints ─────────────────────────────────────────────
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()
        # Migración segura: agrega columnas nuevas si no existen
        _migrate_db()
        from app.models import seed_data, ShopConfig  # noqa: F401 – ensures table creation
        seed_data()

    # Iniciar scheduler solo una vez (evitar doble arranque en modo debug)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _start_scheduler(app)

    return app


def _migrate_db():
    """Agrega columnas nuevas a tablas existentes sin borrar datos."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE staff ADD COLUMN phone VARCHAR(20)",
        "ALTER TABLE services ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE staff ADD COLUMN instagram VARCHAR(100)",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # columna ya existe, ignorar
