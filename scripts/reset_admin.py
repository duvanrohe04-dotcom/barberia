#!/usr/bin/env python3
"""Script sencillo para restablecer la contraseña del usuario `admin`.

Ejecución (desde la raíz del proyecto con la venv activada):
  python scripts/reset_admin.py

El script pedirá la nueva contraseña interactivamente.
"""
import getpass
from app import create_app, db
from app.models import Admin

app = create_app()

def main():
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            print('No se encontró el usuario admin. Lista de admins:')
            for a in Admin.query.all():
                print('-', a.username)
            return

        pw1 = getpass.getpass('Nueva contraseña: ')
        pw2 = getpass.getpass('Confirma nueva contraseña: ')
        if pw1 != pw2:
            print('Las contraseñas no coinciden. Abortando.')
            return
        if len(pw1) < 8:
            print('La contraseña debe tener al menos 8 caracteres. Abortando.')
            return

        admin.set_password(pw1)
        db.session.commit()
        print('Contraseña del admin actualizada correctamente.')

if __name__ == '__main__':
    main()
