from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Admin
from app import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # máx 10 intentos por minuto por IP
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

    admin = Admin.query.filter_by(username=username).first()
    if admin and admin.check_password(password):
        from flask import session
        session.permanent = True
        login_user(admin, remember=True)
        print(f"[Auth] ✅ Login exitoso para '{username}'")
        return jsonify({'success': True})

    # Log para depuración (sin revelar detalles al cliente)
    if not admin:
        print(f"[Auth] ❌ Login fallido: usuario '{username}' no encontrado en BD")
    else:
        print(f"[Auth] ❌ Login fallido: contraseña incorrecta para '{username}'")

    # Mismo mensaje para usuario o contraseña incorrectos (evita enumeración)
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
