from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Appointment, Staff, Service

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    total = Appointment.query.count()
    pending = Appointment.query.filter_by(status='Pendiente').count()
    done = Appointment.query.filter_by(status='Completado').count()
    cancelled = Appointment.query.filter_by(status='Cancelado').count()
    staff_count = Staff.query.filter_by(active=True).count()
    return render_template('admin.html',
                           total=total, pending=pending,
                           done=done, cancelled=cancelled,
                           staff_count=staff_count)
