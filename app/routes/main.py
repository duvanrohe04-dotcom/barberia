from flask import Blueprint, render_template, send_from_directory, current_app, jsonify
from app.models import Service, Staff, Appointment, ShopConfig
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Cargar datos reales de tu base de datos
    male_services = Service.query.filter_by(gender='male', active=True).all()
    female_services = Service.query.filter_by(gender='female', active=True).all()
    barbers = Staff.query.filter_by(gender='male', active=True).all()
    stylists = Staff.query.filter_by(gender='female', active=True).all()
    
    # Cargar TODA tu configuración (fotos de hombre/mujer, logo, etc)
    configs = ShopConfig.query.all()
    conf = {c.key: c.value for c in configs}
    
    return render_template('index.html',
                            male_services=male_services,
                            female_services=female_services,
                            barbers=barbers,
                            stylists=stylists,
                            config=conf, 
                            config_shop_name=conf.get('shop_name', 'JS BARBERSHOP'), 
                            config_shop_logo=conf.get('shop_logo'))

@main_bp.route('/download/android')
def download_android():
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    filepath = os.path.join(downloads_dir, 'app-android.apk')
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'La app para Android aún no está disponible'}), 404
    return send_from_directory(downloads_dir, 'app-android.apk', as_attachment=True)

@main_bp.route('/download/pc')
def download_pc():
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    filepath = os.path.join(downloads_dir, 'app-windows.zip')
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': 'La app para PC aún no está disponible'}), 404
    return send_from_directory(downloads_dir, 'app-windows.zip', as_attachment=True)

@main_bp.route('/sw.js')
def serve_sw():
    return send_from_directory(os.path.join(current_app.root_path, 'static'), 'sw.js', mimetype='application/javascript')

@main_bp.route('/api/download-available')
def download_available():
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    return jsonify({
        'android': os.path.exists(os.path.join(downloads_dir, 'app-android.apk')),
        'pc': os.path.exists(os.path.join(downloads_dir, 'app-windows.zip'))
    })

@main_bp.route('/manifest.json')
def serve_manifest():
    try:
        sn = ShopConfig.query.filter_by(key='shop_name').first()
        sl = ShopConfig.query.filter_by(key='shop_logo').first()
        shop_name = sn.value if sn and sn.value else 'JS Barbershop'
        shop_logo = sl.value if sl and sl.value else None
    except Exception:
        shop_name = 'JS Barbershop'
        shop_logo = None

    logo_url = shop_logo.strip() if shop_logo and shop_logo.strip() else '/static/icons/icon-192.png'
    img_type = "image/png"
    l_low = logo_url.lower()
    if l_low.endswith('.jpg') or l_low.endswith('.jpeg'): img_type = "image/jpeg"
    elif l_low.endswith('.webp'): img_type = "image/webp"
    elif l_low.endswith('.svg'): img_type = "image/svg+xml"

    manifest = {
        "name": shop_name,
        "short_name": shop_name[:14],
        "description": f"Reserva tu cita en {shop_name}",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#d4af37",
        "icons": [{"src": logo_url, "sizes": "192x192", "type": img_type, "purpose": "any"}]
    }
    from flask import make_response, json
    resp = make_response(json.dumps(manifest))
    resp.headers['Content-Type'] = 'application/manifest+json'
    return resp

@main_bp.route('/health')
def health_check():
    try:
        from app.models import db
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
