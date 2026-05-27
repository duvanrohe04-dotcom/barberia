import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Admin
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    try:
        # 1. Eliminar cualquier admin existente (válido o corrupto)
        admins = Admin.query.all()
        print(f"[Fix] Admins encontrados: {len(admins)}")
        for a in admins:
            print(f"  - id={a.id}, username='{a.username}', hash='{a.password_hash[:20] if a.password_hash else 'VACIO'}'...")
            db.session.delete(a)
        db.session.commit()
        print("[Fix] Admins eliminados")

        # 2. Crear admin nuevo con datos correctos
        admin = Admin()
        admin.username = 'admin'
        admin.password_hash = generate_password_hash('barberking2024')
        db.session.add(admin)
        db.session.commit()
        print("[Fix] ✅ Nuevo admin creado: admin / barberking2024")

        # 3. Verificar
        v = Admin.query.first()
        print(f"[Fix] Verificación:")
        print(f"  - id={v.id}")
        print(f"  - username='{v.username}'")
        print(f"  - password_hash='{v.password_hash[:30]}...'")
        print(f"  - check_password('barberking2024'): {v.check_password('barberking2024')}")

    except Exception as e:
        import traceback
        print(f"[Fix] ERROR: {e}")
        traceback.print_exc()
        db.session.rollback()

        # Fallback: SQL directo
        try:
            print("[Fix] Intentando con SQL directo...")
            from sqlalchemy import text
            db.session.execute(text("DELETE FROM admins"))
            db.session.execute(
                text("INSERT INTO admins (username, password_hash) VALUES (:u, :h)"),
                {"u": "admin", "h": generate_password_hash('barberking2024')}
            )
            db.session.commit()
            print("[Fix] ✅ Admin creado vía SQL directo")
        except Exception as e2:
            print(f"[Fix] ERROR también en SQL directo: {e2}")
            db.session.rollback()
