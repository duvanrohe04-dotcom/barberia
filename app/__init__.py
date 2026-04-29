import os
import threading
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

# Lock para evitar race conditions en inicialización de DB
_db_init_lock = threading.Lock()
_db_initialized = False


def weekly_reset(app):
    """Elimina citas completadas/canceladas y todas las reseñas. Conserva citas pendientes."""
    try:
        with app.app_context():
            from app.models import Appointment, Review
            from datetime import datetime
            
            print(f"\n[Reset semanal] ⏰ Iniciando reset semanal a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Eliminar citas completadas y canceladas
            deleted_appts = Appointment.query.filter(
                Appointment.status.in_(['Completado', 'Cancelado'])
            ).delete(synchronize_session=False)
            
            # Eliminar todas las reseñas
            deleted_reviews = Review.query.delete(synchronize_session=False)
            
            db.session.commit()
            
            print(f"[Reset semanal] ✅ Completado:")
            print(f"  - Citas eliminadas: {deleted_appts}")
            print(f"  - Reseñas eliminadas: {deleted_reviews}")
            print(f"[Reset semanal] Dashboard reiniciado correctamente\n")
    except Exception as e:
        print(f"[Reset semanal] ❌ Error: {str(e)}\n")
        db.session.rollback()


def complete_expired_appointments(app):
    """Completa automáticamente las citas que ya pasaron su hora + duración."""
    try:
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
                print(f"[Auto-completar] ✅ {completed_count} cita(s) completada(s) automáticamente")
    except Exception as e:
        print(f"[Auto-completar] ❌ Error: {str(e)}")
        db.session.rollback()


_scheduler = None

def _start_scheduler(app):
    global _scheduler
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Evitar iniciar múltiples schedulers
    if _scheduler is not None and _scheduler.running:
        print("[Scheduler] Ya está en ejecución, no se inicia de nuevo")
        return _scheduler
    
    _scheduler = BackgroundScheduler(daemon=True)
    
    # Completar citas vencidas cada 15 minutos
    _scheduler.add_job(
        func=complete_expired_appointments,
        args=[app],
        trigger=IntervalTrigger(minutes=15),
        id='complete_expired',
        replace_existing=True
    )
    
    # Cada domingo a las 3:00 am
    _scheduler.add_job(
        func=weekly_reset,
        args=[app],
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='weekly_reset',
        replace_existing=True
    )
    
    _scheduler.start()
    print("[Scheduler] ✅ Iniciado correctamente")
    print("[Scheduler] - Completar citas vencidas: cada 15 minutos")
    print("[Scheduler] - Reset semanal: Domingos a las 3:00 AM")
    return _scheduler


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
        global _db_initialized
        with _db_init_lock:
            if not _db_initialized:
                db.create_all()
                try:
                    _migrate_db()
                except Exception as e:
                    print(f"[Migración] Error: {e}")
                from app.models import seed_data, ShopConfig  # noqa: F401
                seed_data()
                _db_initialized = True

    # Iniciar scheduler solo una vez (evitar doble arranque en modo debug)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _start_scheduler(app)

    return app


def _migrate_db():
    """Agrega columnas nuevas a tablas existentes sin borrar datos."""
    from sqlalchemy import text, inspect

    # 1. Primero asegurar que todas las tablas nuevas existan
    db.create_all()

    # 2. Agregar columnas nuevas a tablas existentes
    migrations = [
        "ALTER TABLE staff ADD COLUMN phone VARCHAR(20)",
        "ALTER TABLE services ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE appointments ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "ALTER TABLE staff ADD COLUMN instagram VARCHAR(100)",
        "ALTER TABLE appointments ADD COLUMN is_free_cut BOOLEAN DEFAULT 0",
        "ALTER TABLE appointments ADD COLUMN gender VARCHAR(10) DEFAULT 'male'",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # columna ya existe, ignorar

    # 3. Verificar y crear tablas críticas si no existen (por si db.create_all falló)
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    with db.engine.connect() as conn:
        # Tabla fidelity_progress
        if 'fidelity_progress' not in existing_tables:
            try:
                conn.execute(text("""
                    CREATE TABLE fidelity_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name VARCHAR(100) NOT NULL,
                        client_phone VARCHAR(20) NOT NULL,
                        staff_name VARCHAR(100) NOT NULL,
                        current_cuts INTEGER NOT NULL DEFAULT 0,
                        last_visit VARCHAR(10),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (client_name, client_phone, staff_name)
                    )
                """))
                conn.commit()
                print("[Migración] ✅ Tabla fidelity_progress creada")
            except Exception as e:
                print(f"[Migración] fidelity_progress: {e}")
        else:
            # Limpiar registros con 0 cortes que puedan existir de ciclos anteriores
            try:
                conn.execute(text("DELETE FROM fidelity_progress WHERE current_cuts <= 0"))
                conn.commit()
            except Exception:
                pass

        # Tabla inactive_days
        if 'inactive_days' not in existing_tables:
            try:
                conn.execute(text("""
                    CREATE TABLE inactive_days (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        staff_name VARCHAR(100) NOT NULL,
                        date VARCHAR(10) NOT NULL,
                        reason VARCHAR(200) DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (staff_name, date)
                    )
                """))
                conn.commit()
                print("[Migración] ✅ Tabla inactive_days creada")
            except Exception as e:
                print(f"[Migración] inactive_days: {e}")

        # Tabla reviews (por si acaso)
        if 'reviews' not in existing_tables:
            try:
                conn.execute(text("""
                    CREATE TABLE reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name VARCHAR(100) NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        staff_name VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("[Migración] ✅ Tabla reviews creada")
            except Exception as e:
                print(f"[Migración] reviews: {e}")
