import os
import secrets
from datetime import datetime, timedelta
import threading
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])

_db_init_lock = threading.Lock()
_db_initialized = False

_scheduler = None

def create_app():
    app = Flask(__name__)
    
    # SECRET_KEY desde .env (requerido)
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # Solo para desarrollo local
        if os.environ.get('FLASK_ENV') == 'development':
            secret_key = 'dev-secret-key-change-in-production'
        else:
            raise ValueError("SECRET_KEY no definida. Configúrala en .env")
    app.config['SECRET_KEY'] = secret_key
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    
    # DETECCIÓN INTELIGENTE DE RUTA (Local vs Servidor)
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        # Estamos en local (Windows)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(base_dir, 'instance', 'barberking.db')
        # Crear carpeta instance si no existe
        os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)
        database_url = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    app.config['RATELIMIT_STORAGE_URI'] = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    limiter.init_app(app)

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.context_processor
    def inject_shop_config():
        try:
            from app.models import ShopConfig
            configs = ShopConfig.query.all()
            c_dict = {c.key: c.value for c in configs}
            return dict(
                config=c_dict,
                config_shop_name=c_dict.get('shop_name', 'JS BARBERSHOP'),
                config_shop_logo=c_dict.get('shop_logo')
            )
        except Exception: return dict(config={}, config_shop_name='JS BARBERSHOP', config_shop_logo=None)

    # ── INICIAR SCHEDULER PARA AUTO-COMPLETAR CITAS ──
    _init_scheduler(app)

    with app.app_context():
        global _db_initialized
        with _db_init_lock:
            if not _db_initialized:
                db.create_all()
                _migrate_db()
                _db_initialized = True

    return app


def _init_scheduler(app):
    """Inicializa el APScheduler con jobs de fondo."""
    global _scheduler
    if _scheduler is not None:
        return  # Ya inicializado

    _scheduler = BackgroundScheduler(timezone='America/Bogota')

    def auto_complete_job():
        """Auto-completa citas Pendiente cuya hora de finalización ya pasó."""
        with app.app_context():
            try:
                colombia_tz = pytz.timezone('America/Bogota')
                now = datetime.now(colombia_tz)
                from app.models import Appointment, process_fidelity_for_appointment

                pending = Appointment.query.filter(
                    Appointment.status == 'Pendiente'
                ).all()

                changed = False
                for a in pending:
                    try:
                        h, m = map(int, a.time.split(':'))
                        duration = a.duration_minutes or 60
                        appt_start = datetime.strptime(f"{a.date} {a.time}", "%Y-%m-%d %H:%M")
                        appt_start = colombia_tz.localize(appt_start)
                        appt_end = appt_start + timedelta(minutes=duration)

                        if now >= appt_end:
                            a.status = 'Completado'
                            process_fidelity_for_appointment(a)
                            changed = True
                    except Exception:
                        pass

                if changed:
                    db.session.commit()
                    print(f"[Scheduler] OK - Auto-completadas citas vencidas a las {now.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"[Scheduler] Error auto-completando citas: {e}")

    _scheduler.add_job(
        auto_complete_job,
        'interval',
        minutes=5,
        id='auto_complete_appointments',
        name='Auto-completar citas vencidas',
        replace_existing=True
    )
    _scheduler.start()
    print(f"[Scheduler] OK - Iniciado: auto-completado cada 5 minutos")

def _migrate_db():
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    with db.engine.connect() as conn:
        for table, col, col_type in [
            ("staff", "phone", "VARCHAR(20)"),
            ("services", "duration_minutes", "INTEGER NOT NULL DEFAULT 60"),
            ("appointments", "duration_minutes", "INTEGER NOT NULL DEFAULT 60"),
            ("staff", "instagram", "VARCHAR(100)"),
            ("appointments", "is_free_cut", "BOOLEAN DEFAULT FALSE"),
            ("appointments", "gender", "VARCHAR(10) DEFAULT 'male'"),
            ("appointments", "reminder_sent", "BOOLEAN DEFAULT FALSE"),
        ]:
            if table in tables:
                cols = [c['name'] for c in inspector.get_columns(table)]
                if col not in cols:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        conn.commit()
                    except Exception: pass
