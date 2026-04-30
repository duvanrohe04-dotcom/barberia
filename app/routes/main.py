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
