import os
from datetime import datetime, timedelta
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
    """Elimina citas completadas/canceladas y reseñas. Conserva citas pendientes y tarjetas de fidelidad activas."""
    try:
        with app.app_context():
            from app.models import Appointment, Review, InactiveDay
            from datetime import datetime, date

            now = datetime.now()
            print(f"\n[Reset semanal] Iniciando reset semanal a las {now.strftime('%Y-%m-%d %H:%M:%S')}")

            # Eliminar citas completadas y canceladas
            deleted_appts = Appointment.query.filter(
                Appointment.status.in_(['Completado', 'Cancelado'])
            ).delete(synchronize_session=False)

            # Eliminar todas las reseñas
            deleted_reviews = Review.query.delete(synchronize_session=False)

            # Eliminar días inactivos que ya pasaron (mantener solo futuros)
            today_str = date.today().isoformat()
            deleted_inactive = InactiveDay.query.filter(
                InactiveDay.date < today_str
            ).delete(synchronize_session=False)

            db.session.commit()

            print(f"[Reset semanal] Completado:")
            print(f"  - Citas eliminadas: {deleted_appts}")
            print(f"  - Reseñas eliminadas: {deleted_reviews}")
            print(f"  - Días inactivos pasados eliminados: {deleted_inactive}")
            print(f"[Reset semanal] Dashboard reiniciado correctamente\n")
    except Exception as e:
        print(f"[Reset semanal] Error: {str(e)}\n")
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            pass


def complete_expired_appointments(app):
    """Completa automáticamente las citas que ya pasaron su hora + duración."""
    try:
        with app.app_context():
            from app.models import Appointment
            from datetime import datetime, date

            now = datetime.now()
            today_str = date.today().isoformat()

            # Obtener citas pendientes de hoy o días anteriores
            expired = Appointment.query.filter(
                Appointment.status == 'Pendiente',
                Appointment.date <= today_str
            ).all()

            completed_count = 0
            for appt in expired:
                try:
                    h, m = map(int, appt.time.split(':'))
                    duration = appt.duration_minutes or 60
                    # Construir datetime completo de fin de la cita
                    from datetime import datetime as dt
                    appt_start = dt.strptime(f"{appt.date} {appt.time}", "%Y-%m-%d %H:%M")
                    appt_end = appt_start.replace(
                        hour=(h * 60 + m + duration) // 60,
                        minute=(h * 60 + m + duration) % 60
                    )
                    # Si ya pasó la hora de finalización, completar
                    if now >= appt_end:
                        if appt.status != 'Completado':
                            appt.status = 'Completado'
                            from app.models import process_fidelity_for_appointment
                            process_fidelity_for_appointment(appt)
                            completed_count += 1
                except Exception:
                    pass

            if completed_count > 0:
                db.session.commit()
                print(f"[Auto-completar] {completed_count} cita(s) completada(s) automáticamente")
    except Exception as e:
        print(f"[Auto-completar] Error: {str(e)}")
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            pass


def send_appointment_reminders(app):
    """Envía recordatorios de WhatsApp 20 minutos antes de la cita."""
    try:
        with app.app_context():
            from app.models import Appointment, ShopConfig
            from app.whatsapp_service import send_reminder_to_client
            from datetime import datetime, timedelta

            # Buscar citas de hoy que ocurran en los próximos 20-25 minutos y no tengan recordatorio enviado
            now = datetime.now()
            target_time = now + timedelta(minutes=20)
            
            today_str = now.date().isoformat()
            
            # Obtener nombre de la tienda
            name_row = ShopConfig.query.filter_by(key='shop_name').first()
            s_name = name_row.value if name_row and name_row.value else 'Barbería'

            # Consultar citas pendientes para hoy que no han enviado recordatorio
            pending = Appointment.query.filter(
                Appointment.status == 'Pendiente',
                Appointment.date == today_str,
                Appointment.reminder_sent == False
            ).all()

            sent_count = 0
            for appt in pending:
                try:
                    # Convertir hora de cita a datetime
                    h, m = map(int, appt.time.split(':'))
                    appt_dt = datetime.strptime(f"{appt.date} {appt.time}", "%Y-%m-%d %H:%M")
                    
                    # Si faltan entre 0 y 25 minutos para la cita, enviar recordatorio
                    # Usamos un rango para no perder citas si el scheduler corre cada 5 min
                    time_diff = (appt_dt - now).total_seconds() / 60
                    
                    if 0 <= time_diff <= 25:
                        send_reminder_to_client(appt, s_name)
                        appt.reminder_sent = True
                        sent_count += 1
                except Exception:
                    pass

            if sent_count > 0:
                db.session.commit()
                print(f"[Recordatorios] {sent_count} recordatorio(s) enviado(s) automáticamente")
    except Exception as e:
        try:
            with app.app_context():
                db.session.rollback()
        except Exception:
            pass
        print(f"[Recordatorios] Error: {str(e)}")


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
    
    _scheduler.add_job(
        func=send_appointment_reminders,
        trigger="interval",
        minutes=5,
        args=[app],
        id="whatsapp_reminders"
    )

    _scheduler.start()
    print("[Scheduler] Iniciado correctamente")
    print("[Scheduler] - Completar citas vencidas: cada 15 minutos")
    print("[Scheduler] - Limpieza semanal (Domingo 3 AM)")
    print("[Scheduler] - Recordatorios WhatsApp: cada 5 minutos")
    return _scheduler


def create_app():
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo para uploads

    # Usará SQLite localmente por defecto. En producción (Railway/Render) usará la variable de entorno DATABASE_URL
    default_db = 'sqlite:///barberking.db'
    database_url = os.environ.get('DATABASE_URL', default_db)
    
    # Soporte para la URL de Postgres (convierte postgres:// a postgresql:// para SQLAlchemy)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Opciones de pool solo para bases de datos que lo soportan (PostgreSQL, MySQL)
    # SQLite no soporta pool_size ni max_overflow
    if not database_url.startswith('sqlite'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'max_overflow': 20,
        }
    else:
        # SQLite: solo check_same_thread=False para evitar errores con múltiples threads
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'check_same_thread': False},
            'pool_pre_ping': True,
        }
    
    # Configuración de sesiones y cookies
    # En desarrollo (localhost), permitir cookies sin HTTPS
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('DATABASE_URL', '').startswith('postgresql')
    
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = is_production  # Solo HTTPS en producción
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['REMEMBER_COOKIE_SECURE'] = is_production  # Solo HTTPS en producción
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['SESSION_PERMANENT'] = True

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

    # ── Rate Limiting ──────────────────────────────────────────
    app.config['RATELIMIT_STORAGE_URI'] = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
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

    @app.context_processor
    def inject_shop_config():
        try:
            from app.models import ShopConfig
            shop_name_row = ShopConfig.query.filter_by(key='shop_name').first()
            shop_logo_row = ShopConfig.query.filter_by(key='shop_logo').first()
            return dict(
                config_shop_name=shop_name_row.value if shop_name_row and shop_name_row.value else 'BarberKing | Barbería & Estilismo',
                config_shop_logo=shop_logo_row.value if shop_logo_row and shop_logo_row.value else None
            )
        except Exception:
            return dict(
                config_shop_name='BarberKing | Barbería & Estilismo',
                config_shop_logo=None
            )

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
                from app import models  # Asegurar que todos los modelos se carguen antes de create_all
                db.create_all()
                try:
                    _migrate_db()
                except Exception as e:
                    print(f"[Migración] Error: {e}")
                from app.models import seed_data, ShopConfig  # noqa: F401
                seed_data()
                _db_initialized = True

    # Iniciar scheduler solo en el proceso principal (no en workers de gunicorn)
    # WERKZEUG_RUN_MAIN=true → proceso recargado en dev
    # SERVER_SOFTWARE no definido → proceso principal en producción con gunicorn
    is_main_process = (
        not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    )
    # En gunicorn, solo el worker con GUNICORN_WORKER_ID=0 o sin esa variable arranca el scheduler
    worker_id = os.environ.get('GUNICORN_WORKER_ID', '0')
    if is_main_process and worker_id == '0':
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
        "ALTER TABLE appointments ADD COLUMN is_free_cut BOOLEAN DEFAULT FALSE",
        "ALTER TABLE appointments ADD COLUMN gender VARCHAR(10) DEFAULT 'male'",
        "ALTER TABLE appointments ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE",
    ]
    with db.engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # columna ya existe, ignorar

    # 3. Inicializar ShopConfig con valores por defecto si no existen
    from app.models import ShopConfig
    default_configs = [
        ('shop_name', 'BarberKing'),
        ('shop_logo', ''),
        ('ubicacion', '📍 Bogotá, Colombia'),
        ('telefono', '+57 310 000 0000'),
        ('wa', ''),
        ('ig', ''),
        ('wa_sty', ''),
        ('ig_sty', ''),
        ('evo_instance', 'barberking')
    ]
    for k in ['shop_name', 'shop_logo', 'wa_sty', 'ig_sty', 'evo_instance']:
        if not ShopConfig.query.filter_by(key=k).first():
            db.session.add(ShopConfig(key=k, value='jsbarbershop' if k=='evo_instance' else ''))
    db.session.commit()

    # 4. Verificar y crear tablas críticas...
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
                print("[Migración] Tabla fidelity_progress creada")
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
                print("[Migración] Tabla inactive_days creada")
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
                print("[Migración] Tabla reviews creada")
            except Exception as e:
                print(f"[Migración] reviews: {e}")
