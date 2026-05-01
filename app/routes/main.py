from flask import Blueprint, render_template, send_from_directory, current_app, jsonify
from app.models import Service, Staff, Appointment
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    male_services = Service.query.filter_by(gender='male', active=True).all()
    female_services = Service.query.filter_by(gender='female', active=True).all()
    barbers = Staff.query.filter_by(gender='male', active=True).all()
    stylists = Staff.query.filter_by(gender='female', active=True).all()
    return render_template('index.html',
                            male_services=male_services,
                            female_services=female_services,
                            barbers=barbers,
                            stylists=stylists)


@main_bp.route('/download/android')
def download_android():
    """Descarga la app para Android (APK)."""
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    filepath = os.path.join(downloads_dir, 'app-android.apk')
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'La app para Android aún no está disponible'}), 404
    return send_from_directory(downloads_dir, 'app-android.apk', as_attachment=True)


@main_bp.route('/download/pc')
def download_pc():
    """Descarga la app para PC (ZIP o EXE)."""
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    filepath = os.path.join(downloads_dir, 'app-windows.zip')
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'La app para PC aún no está disponible'}), 404
    return send_from_directory(downloads_dir, 'app-windows.zip', as_attachment=True)


@main_bp.route('/sw.js')
def serve_sw():
    """Sirve el Service Worker desde la raíz para controlar toda la PWA."""
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'sw.js', mimetype='application/javascript')


@main_bp.route('/api/download-available')
def download_available():
    """Verifica si los archivos de descarga están disponibles."""
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    return jsonify({
        'android': os.path.exists(os.path.join(downloads_dir, 'app-android.apk')),
        'pc': os.path.exists(os.path.join(downloads_dir, 'app-windows.zip'))
    })


@main_bp.route('/manifest.json')
def serve_manifest():
    """Sirve un manifest.json dinámico con el logo y nombre configurados por el admin."""
    try:
        from app.models import ShopConfig
        shop_name_row = ShopConfig.query.filter_by(key='shop_name').first()
        shop_logo_row = ShopConfig.query.filter_by(key='shop_logo').first()
        
        shop_name = shop_name_row.value if shop_name_row and shop_name_row.value else 'BarberKing'
        shop_logo = shop_logo_row.value if shop_logo_row and shop_logo_row.value else '/static/icons/icon-192.png'
    except Exception:
        shop_name = 'BarberKing'
        shop_logo = '/static/icons/icon-192.png'
        
    # Determinar el tipo de imagen dinámicamente
    img_type = "image/png"
    if shop_logo.lower().endswith('.jpg') or shop_logo.lower().endswith('.jpeg'):
        img_type = "image/jpeg"
    elif shop_logo.lower().endswith('.webp'):
        img_type = "image/webp"

    manifest = {
        "name": shop_name,
        "short_name": shop_name[:12], # Nombre corto para que no se corte en el móvil
        "description": f"Aplicación oficial de {shop_name}",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#d4af37",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": shop_logo,
                "sizes": "192x192",
                "type": img_type,
                "purpose": "any"
            },
            {
                "src": shop_logo,
                "sizes": "512x512",
                "type": img_type,
                "purpose": "maskable"
            }
        ]
    }
    return jsonify(manifest)


@main_bp.route('/health')
def health_check():
    """Endpoint de salud para Coolify, Docker y balanceadores de carga."""
    try:
        from app.models import db
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500
