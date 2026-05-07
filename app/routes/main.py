from flask import Blueprint, render_template, send_from_directory, current_app, jsonify
from app.models import Service, Staff, Appointment
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    from app.models import ShopConfig
    male_services = Service.query.filter_by(gender='male', active=True).all()
    female_services = Service.query.filter_by(gender='female', active=True).all()
    barbers = Staff.query.filter_by(gender='male', active=True).all()
    stylists = Staff.query.filter_by(gender='female', active=True).all()
    sn = ShopConfig.query.filter_by(key='shop_name').first()
    sl = ShopConfig.query.filter_by(key='shop_logo').first()
    conf = {'shop_name': sn.value if sn and sn.value else 'BARBERSTYLEPRO', 'shop_logo': sl.value if sl and sl.value else None}
    return render_template('index.html',
                            male_services=male_services,
                            female_services=female_services,
                            barbers=barbers,
                            stylists=stylists,
                            config=conf, config_shop_name=conf['shop_name'], config_shop_logo=conf['shop_logo'])


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

        shop_name = shop_name_row.value if shop_name_row and shop_name_row.value else 'JS Barbershop'
        shop_logo = shop_logo_row.value if shop_logo_row and shop_logo_row.value else None
    except Exception:
        shop_name = 'JS Barbershop'
        shop_logo = None

    # Usar logo configurado o el icono por defecto
    logo_url = shop_logo.strip() if shop_logo and shop_logo.strip() else '/static/icons/icon-192.png'

    # Determinar el tipo de imagen
    img_type = "image/png"
    logo_lower = logo_url.lower()
    if logo_lower.endswith('.jpg') or logo_lower.endswith('.jpeg'):
        img_type = "image/jpeg"
    elif logo_lower.endswith('.webp'):
        img_type = "image/webp"
    elif logo_lower.endswith('.svg'):
        img_type = "image/svg+xml"

    manifest = {
        "name": shop_name,
        "short_name": shop_name[:14],
        "description": f"Reserva tu cita en {shop_name} — Barbería & Estilismo",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#d4af37",
        "orientation": "portrait-primary",
        "lang": "es",
        "icons": [
            {"src": logo_url, "sizes": "192x192", "type": img_type, "purpose": "any"},
            {"src": logo_url, "sizes": "192x192", "type": img_type, "purpose": "maskable"},
            {"src": logo_url, "sizes": "512x512", "type": img_type, "purpose": "any"},
            {"src": logo_url, "sizes": "512x512", "type": img_type, "purpose": "maskable"}
        ]
    }
    from flask import make_response, json
    resp = make_response(json.dumps(manifest))
    resp.headers['Content-Type'] = 'application/manifest+json'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp



@main_bp.route('/health')
def health_check():
    """Endpoint de salud para Coolify, Docker y balanceadores de carga."""
    try:
        from app.models import db
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500
