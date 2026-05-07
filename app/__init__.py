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

_db_init_lock = threading.Lock()
_db_initialized = False

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'barberking_super_secret_key_fixed')
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

    with app.app_context():
        global _db_initialized
        with _db_init_lock:
            if not _db_initialized:
                db.create_all()
                _migrate_db()
                _db_initialized = True

    return app

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
