import os
import secrets
import sys
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

# Cargar primero .env.local (si existe) y luego .env para compatibilidad local y Coolify.
load_dotenv('.env.local', override=False)
load_dotenv('.env', override=False)

db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])

_db_init_lock = threading.Lock()
_db_initialized = False

_scheduler = None

def create_app():
    app = Flask(__name__)
    
    # SECRET_KEY (requerido en producción; para desarrollo se genera si no existe)
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if sys.platform == 'win32' or os.environ.get('FLASK_ENV') == 'development':
            # Generar una clave temporal para desarrollo si no se proporciona
            secret_key = os.environ.get('DEV_SECRET_KEY') or secrets.token_hex(32)
            print("[WARN] Usando SECRET_KEY temporal (desarrollo). Define SECRET_KEY en .env para estabilidad de sesiones.")
        else:
            raise ValueError("SECRET_KEY no definida")
    app.config['SECRET_KEY'] = secret_key
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    
    # DETECCIÓN: Windows siempre usa SQLite; Linux/Docker usa PostgreSQL
    if sys.platform == 'win32':
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        db_path = os.path.join(base_dir, 'instance', 'barberking.db')
        os.makedirs(os.path.join(base_dir, 'instance'), exist_ok=True)
        database_url = f'sqlite:///{db_path}'
    else:
        # NOTA: Se construye SIEMPRE desde variables individuales para evitar
        # que Coolify inyecte una DATABASE_URL con credenciales incorrectas.
        pg_user = os.environ.get('POSTGRES_USER', 'barber_user')
        pg_pass = os.environ.get('POSTGRES_PASSWORD', 'julyanna231101')
        pg_host = os.environ.get('POSTGRES_HOST', 'postgres-db')
        pg_port = os.environ.get('POSTGRES_PORT', '5432')
        pg_db = os.environ.get('POSTGRES_DB', 'barberking_db')
        database_url = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
    }
    
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

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'success': False, 'message': 'Demasiados intentos. Espera un minuto.'}), 429

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
                _ensure_db_setup()
                db.create_all()
                _migrate_db()
                from app.models import seed_data
                try:
                    seed_data()
                except Exception as e:
                    print(f"[Seed] Error en seed_data: {e}")

                from app.models import Admin
                _ensure_admin_startup()

                _db_initialized = True

    return app


def _ensure_db_setup():
    """Crea roles faltantes (admin, barber_user) y evolution_db en cada inicio."""
    if sys.platform == 'win32':
        return

    import psycopg2
    from sqlalchemy import create_engine, text

    pg_host = os.environ.get('POSTGRES_HOST', 'postgres-db')
    pg_port = os.environ.get('POSTGRES_PORT', '5432')
    pg_db = os.environ.get('POSTGRES_DB', 'barberking_db')

    env_pass = os.environ.get('POSTGRES_PASSWORD')
    evo_pass = os.environ.get('EVOLUTION_DB_PASSWORD')
    evo_db = os.environ.get('EVOLUTION_DB_NAME', 'evolution_db')

    # Construir combinaciones de usuarios/contraseñas basadas en variables de entorno
    users = ['barber_user', 'admin', 'postgres']
    passwords = [env_pass, evo_pass, os.environ.get('POSTGRES_PASSWORD', '')]
    creds_to_try = []
    for u in users:
        for p in passwords:
            if p is None:
                continue
            creds_to_try.append((u, p))

    for su_user, su_pass in creds_to_try:
        if not su_user or su_pass is None:
            continue
        try:
            su_url = f'postgresql://{su_user}:{su_pass}@{pg_host}:{pg_port}/{pg_db}'
            eng = create_engine(su_url, connect_args={'connect_timeout': 3})
            with eng.connect() as conn:
                # Crear roles si no existen. No establecer contraseñas hardcodeadas; preferir manejo vía variables/administración DB.
                conn.execute(text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
                            CREATE ROLE admin LOGIN;
                        END IF;
                        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'barber_user') THEN
                            CREATE ROLE barber_user LOGIN;
                        END IF;
                    END
                    $$;
                """))
                conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
                conn.commit()
            eng.dispose()
            # Crear evolution_db si no existe
            try:
                c = psycopg2.connect(host=pg_host, port=pg_port, user=su_user, password=su_pass, dbname='postgres', connect_timeout=3)
                c.autocommit = True
                cur = c.cursor()
                cur.execute(f'CREATE DATABASE "{evo_db}"')
                cur.close()
                c.close()
            except Exception:
                pass
            print(f"[DB] Setup OK: roles asegurados, evolution_db listo")
            return
        except Exception as e:
            print(f"[DB] Intento {su_user} falló: {e}")
            continue


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

def _ensure_admin_startup():
    """Crea admin SOLO si no existe. NO sobreescribe credenciales existentes."""
    from app.models import Admin
    import os
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            admin = Admin.query.order_by(Admin.id).first()
            if not admin:
                admin = Admin(username='admin')
                admin.set_password('barberking2024')
                db.session.add(admin)
                db.session.commit()
                print("[Admin] ✅ Admin creado: admin/barberking2024")
            else:
                # Si ADMIN_RESET=true, forzar reset
                if os.environ.get('ADMIN_RESET', '').lower() == 'true':
                    admin.username = 'admin'
                    admin.set_password('barberking2024')
                    db.session.commit()
                    print("[Admin] ✅ Admin reset forzoso (ADMIN_RESET=true)")
                else:
                    print(f"[Admin] Admin ya existe (username={admin.username}), se respetan credenciales actuales")
            return
        except Exception as e:
            db.session.rollback()
            print(f"[Admin] ❌ Intento {attempt}/{max_retries} falló: {e}")
            if attempt < max_retries:
                import time
                time.sleep(2)
    print("[Admin] ❌ No se pudo crear admin tras todos los intentos")


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
