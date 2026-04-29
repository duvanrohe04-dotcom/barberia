from flask import Blueprint, render_template, send_from_directory
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
    return send_from_directory('static/downloads', 'app-android.apk', as_attachment=True)


@main_bp.route('/download/pc')
def download_pc():
    """Descarga la app para PC (ZIP o EXE)."""
    return send_from_directory('static/downloads', 'app-windows.zip', as_attachment=True)
