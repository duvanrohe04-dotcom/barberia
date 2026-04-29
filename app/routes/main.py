from flask import Blueprint, render_template
from app.models import Service, Staff, Appointment

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
