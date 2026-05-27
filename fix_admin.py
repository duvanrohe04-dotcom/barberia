import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Admin

app = create_app()

with app.app_context():
    try:
        admin = Admin.query.order_by(Admin.id).first()
        if not admin:
            admin = Admin(username='admin')
            db.session.add(admin)
            print("[Fix] Admin no existía - creado nuevo")
        else:
            print(f"[Fix] Admin existente: id={admin.id}, username='{admin.username}'")

        admin.set_password('barberking2024')
        db.session.commit()
        print("[Fix] Admin actualizado: admin / barberking2024")

        # Verificar
        verify = Admin.query.order_by(Admin.id).first()
        print(f"[Fix] Verificación - Admin existe: {verify is not None}")
        if verify:
            print(f"[Fix] Username: '{verify.username}'")
            print(f"[Fix] Password válida: {verify.check_password('barberking2024')}")
    except Exception as e:
        import traceback
        print(f"[Fix] ERROR: {e}")
        traceback.print_exc()
        db.session.rollback()
