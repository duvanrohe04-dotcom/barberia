from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from app.models import db, Admin
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)


def _ensure_admin(password=None):
    """Crea admin SOLO si no existe. NO sobreescribe credenciales existentes.
    Retorna el admin encontrado/creado, o None si falla."""
    import os
    import secrets
    try:
        admin = Admin.query.order_by(Admin.id).first()
        if admin:
            return admin
        admin_username = os.environ.get('ADMIN_USER', 'admin')
        admin_password = password or os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            print('[Auth] WARNING: ADMIN_PASSWORD not set; generated temporary admin password.')
        admin = Admin(username=admin_username)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"[Auth] ✅ Admin creado automáticamente: {admin_username}/(generated or env password)")
        return admin
    except Exception as e:
        db.session.rollback()
        print(f"[Auth] ❌ Error creando admin: {e}")
        return None


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'GET':
        from flask import redirect
        return redirect('/')

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Datos inválidos'}), 400

    username = str(data.get('username', '')).strip()[:80]
    password = str(data.get('password', ''))[:200]

    if not username or not password:
        return jsonify({'success': False, 'message': 'Credenciales requeridas'}), 400

    admin = Admin.query.filter(func.lower(Admin.username) == username.casefold()).first()
    if not admin:
        admin = Admin.query.order_by(Admin.id).first()

    if admin and admin.check_password(password):
        from flask import session
        session.permanent = True
        login_user(admin, remember=True)
        print(f"[Auth] ✅ Login exitoso para '{username}'")
        return jsonify({'success': True})

    # Si falló la autenticación, intentar reparar admin automáticamente
    # (por si el seed de inicio no funcionó o la DB fue recreada)
    try:
        fixed_admin = _ensure_admin(password)
        if fixed_admin and fixed_admin.check_password(password):
            from flask import session
            session.permanent = True
            login_user(fixed_admin, remember=True)
            print(f"[Auth] ✅ Login exitoso (reparado) para '{username}'")
            return jsonify({'success': True})
    except Exception as e:
        print(f"[Auth] ❌ Error en reparación automática: {e}")

    if not admin:
        print(f"[Auth] ❌ Login fallido: usuario '{username}' no encontrado en BD")
    else:
        print(f"[Auth] ❌ Login fallido: contraseña incorrecta para '{username}'")

    return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})


@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Verificar si hay una sesión activa de administrador."""
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'username': current_user.username})
    return jsonify({'authenticated': False})


@auth_bp.route('/update-credentials', methods=['POST'])
@login_required
def update_credentials():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Datos inválidos'}), 400
    username = str(data.get('username', '')).strip()[:80]
    password = str(data.get('password', ''))[:200]
    old_password = str(data.get('old_password', ''))
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña requeridos'}), 400
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 8 caracteres'}), 400
    
    admin = Admin.query.get(current_user.id)
    if not admin.check_password(old_password):
        return jsonify({'success': False, 'message': 'La contraseña actual es incorrecta'}), 401
    
    admin.username = username
    admin.set_password(password)
    db.session.commit()
    return jsonify({'success': True})
