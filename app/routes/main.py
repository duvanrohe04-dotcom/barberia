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


@main_bp.route('/health')
def health():
    """Endpoint de healthcheck para Coolify y monitoreo."""
    try:
        # Verificar que la base de datos responde
        Service.query.first()
        return jsonify({
            'status': 'healthy',
            'service': 'JS Barbershop',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@main_bp.route('/download/android')
def download_android():
    """Descarga la app para Android (APK)."""
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    return send_from_directory(downloads_dir, 'app-android.apk', as_attachment=True)


@main_bp.route('/download/pc')
def download_pc():
    """Descarga la app para PC (ZIP o EXE)."""
    downloads_dir = os.path.join(current_app.root_path, 'static', 'downloads')
    return send_from_directory(downloads_dir, 'app-windows.zip', as_attachment=True)
