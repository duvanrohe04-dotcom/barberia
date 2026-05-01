from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import db, Service, Staff, Appointment, ShopConfig, Review
from app import limiter
import re, os, uuid

api_bp = Blueprint('api', __name__)

# ── Helpers de validación ──────────────────────────────────────

def _safe_str(val, max_len=200):
    return str(val or '').strip()[:max_len]

def _valid_date(d):
    return bool(d and re.match(r'^\d{4}-\d{2}-\d{2}$', d))

def _valid_time(t):
    return bool(t and re.match(r'^\d{2}:\d{2}$', t))

def _allowed_time(date_str, time_str, gender):
    """Valida que la hora esté dentro del horario permitido para ese día y género.
    
    HORARIOS:
    Hombres:
      - Lun-Vie: 8am-11am y 2pm-8pm
      - Sábado: 8am-8pm (corrido)
      - Domingo: 8am-12pm
    
    Mujeres:
      - Lun-Vie: 9am-11am y 2pm-8pm
      - Sábado: 9am-8pm (corrido)
      - Domingo: NO HAY SERVICIO
    """
    try:
        from datetime import date as dt_date
        d = dt_date.fromisoformat(date_str)
        dow = d.weekday()  # 0=lunes, 1=martes, ..., 5=viernes, 6=sábado, 7=domingo
        h = int(time_str.split(':')[0])
        m = int(time_str.split(':')[1])
        total = h * 60 + m
        
        # Validar que sea un slot válido de 15 minutos
        if m % 15 != 0:
            return False
        
        # Domingo (dow == 6 en weekday)
        if dow == 6:
            if gender == 'female':
                return False  # Mujeres: no hay servicio los domingos
            return 8*60 <= total < 12*60  # Hombres: 8am-12pm
        
        # Sábado (dow == 5 en weekday)
        if dow == 5:
            start = 9*60 if gender == 'female' else 8*60
            return start <= total < 20*60  # Corrido hasta 8pm
        
        # Lunes a Viernes (dow 0-4)
        start_morning = 9*60 if gender == 'female' else 8*60
        # Mañana: 8am/9am - 11am, Tarde: 2pm - 8pm
        return (start_morning <= total < 11*60) or (14*60 <= total < 20*60)
        
    except Exception:
        return False

def _valid_phone(p):
    return bool(p and re.match(r'^\d{7,15}$', p.replace(' ', '').replace('+', '')))

# ── IMAGE UPLOAD ──────────────────────────────────────────────

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@api_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'success': False, 'message': 'No se recibió archivo'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
    if ext not in ALLOWED_EXT:
        return jsonify({'success': False, 'message': 'Tipo de archivo no permitido'}), 400
    filename = uuid.uuid4().hex + '.' + ext
    upload_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    f.save(os.path.join(upload_dir, filename))
    return jsonify({'success': True, 'url': f'/static/uploads/{filename}'})


# ── APPOINTMENTS ──────────────────────────────────────────────

@api_bp.route('/appointments/fidelity', methods=['GET'])
def get_fidelity_count():
    """Obtiene el conteo de reservas acumuladas para fidelidad (solo barberos)."""
    name  = _safe_str(request.args.get('name', ''), 100).lower()
    phone = _safe_str(request.args.get('phone', ''), 20)
    staff_name = _safe_str(request.args.get('staff', ''), 100)
    
    if not name or not phone or not staff_name:
        return jsonify({'count': 0, 'message': 'Faltan datos'})
    
    # Buscar en la tabla de progreso de fidelidad
    from app.models import FidelityProgress
    progress = FidelityProgress.query.filter(
        db.func.lower(FidelityProgress.client_name) == name,
        FidelityProgress.client_phone == phone,
        FidelityProgress.staff_name == staff_name
    ).first()
    
    count = progress.current_cuts if progress else 0
    
    return jsonify({
        'count': count, 
        'message': 'ok'
    })


@api_bp.route('/appointments/fidelity/cards', methods=['GET'])
@login_required
def get_fidelity_cards():
    """Obtiene todas las tarjetas de fidelidad activas (solo barberos)."""
    from app.models import FidelityProgress
    
    # Mostrar todos los clientes con al menos 1 corte, ordenados por número de cortes (mayor a menor)
    progress_records = FidelityProgress.query.filter(
        FidelityProgress.current_cuts >= 1
    ).order_by(FidelityProgress.current_cuts.desc()).all()    
    # Convertir a formato esperado por el frontend
    result = []
    for record in progress_records:
        result.append({
            'name': record.client_name,
            'phone': record.client_phone,
            'staff': record.staff_name,
            'count': record.current_cuts,
            'last_visit': record.last_visit
        })
    
    return jsonify({'cards': result, 'total': len(result)})


@api_bp.route('/appointments', methods=['GET'])
@login_required
def get_appointments():
    # El scheduler ya completa las citas vencidas cada 15 minutos
    # Solo retornar las citas ordenadas
    appts = Appointment.query.order_by(Appointment.date, Appointment.time).all()
    return jsonify([_appt_dict(a) for a in appts])


@api_bp.route('/appointments', methods=['POST'])
@limiter.limit("30 per minute")
def create_appointment():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Datos inválidos'}), 400

    name  = _safe_str(data.get('client_name'), 100)
    phone = _safe_str(data.get('client_phone'), 20)
    gender = _safe_str(data.get('gender'), 10)
    service_name = _safe_str(data.get('service_name'), 100)
    staff_name   = _safe_str(data.get('staff_name'), 100)
    date  = _safe_str(data.get('date'), 10)
    time  = _safe_str(data.get('time'), 5)
    total = _safe_str(data.get('total'), 30)

    if not all([name, phone, gender, service_name, staff_name, date, time]):
        return jsonify({'success': False, 'message': 'Faltan campos requeridos'}), 400
    if gender not in ('male', 'female'):
        return jsonify({'success': False, 'message': 'Género inválido'}), 400
    if not _valid_date(date):
        return jsonify({'success': False, 'message': 'Fecha inválida'}), 400
    if not _valid_time(time):
        return jsonify({'success': False, 'message': 'Hora inválida'}), 400
    if not _allowed_time(date, time, gender):
        msg = 'Los domingos no hay servicio de estilismo. Por favor elige otro día.' if gender=='female' else 'Esa hora está fuera del horario de atención.'
        return jsonify({'success': False, 'message': msg}), 400
    if not _valid_phone(phone):
        return jsonify({'success': False, 'message': 'Teléfono inválido'}), 400

    # VERIFICAR SI EL EMPLEADO ESTÁ INACTIVO ESE DÍA
    from app.models import InactiveDay
    inactive = InactiveDay.query.filter_by(staff_name=staff_name, date=date).first()
    if inactive:
        reason = f" ({inactive.reason})" if inactive.reason else ""
        return jsonify({
            'success': False, 
            'message': f"❌ Lo sentimos, {staff_name} no está disponible el {date}{reason}.\n\n💡 Te sugerimos:\n• Elige otra fecha\n• Reserva con otro profesional\n\n¡Gracias por tu comprensión!",
            'staff_inactive': True
        }), 409

    # Validar que no sea fecha/hora del pasado (con margen de 5 minutos)
    from datetime import datetime, timedelta
    try:
        appointment_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        now_with_margin = datetime.now() + timedelta(minutes=5)
        if appointment_datetime < now_with_margin:
            return jsonify({'success': False, 'message': 'No puedes reservar una cita en el pasado'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de fecha u hora inválido'}), 400

    # Obtener duración del servicio nuevo
    srv = Service.query.filter_by(name=service_name).first()
    duration = srv.duration_minutes if srv else 60

    # Verificar conflictos considerando duración de citas existentes y la nueva
    h_new, m_new = map(int, time.split(':'))
    new_start = h_new * 60 + m_new
    new_end   = new_start + duration

    existing = Appointment.query.filter_by(
        date=date, staff_name=staff_name
    ).filter(Appointment.status != 'Cancelado').all()

    for ex in existing:
        eh, em = map(int, ex.time.split(':'))
        ex_start = eh * 60 + em
        ex_end   = ex_start + (ex.duration_minutes or 60)
        # Hay conflicto si los rangos se solapan
        if new_start < ex_end and new_end > ex_start:
            return jsonify({'success': False, 'message': 'Ese horario se cruza con una cita existente'}), 409

    appt = Appointment(
        client_name=name, client_phone=phone, gender=gender,
        service_name=service_name, staff_name=staff_name,
        date=date, time=time, duration_minutes=duration,
        total=total, status='Pendiente'
    )
    db.session.add(appt)
    db.session.commit()

    # --- NOTIFICACIÓN AUTOMÁTICA WHATSAPP ---
    try:
        from app.whatsapp_service import notify_admin_new_appointment
        from app.models import ShopConfig
        name_row = ShopConfig.query.filter_by(key='shop_name').first()
        s_name = name_row.value if name_row and name_row.value else 'Barbería'
        notify_admin_new_appointment(appt, s_name)
    except Exception as e:
        print(f"[WhatsApp] Error en notificación inicial: {e}")
    # ----------------------------------------

    return jsonify({'success': True, 'appointment': _appt_dict(appt)}), 201


@api_bp.route('/appointments/<int:appt_id>/cancel', methods=['POST'])
@limiter.limit("20 per minute")
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.status == 'Cancelado':
        return jsonify({'success': False, 'message': 'Ya está cancelada'}), 400
    appt.status = 'Cancelado'
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/appointments/<int:appt_id>/complete', methods=['POST'])
@limiter.limit("20 per minute")
def complete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if appt.status == 'Completado':
        return jsonify({'success': False, 'message': 'Ya está completada'}), 400
    
    appt.status = 'Completado'
    
    # Actualizar progreso de fidelidad solo para barbería (género masculino)
    from app.models import process_fidelity_for_appointment
    process_fidelity_for_appointment(appt)
    
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/appointments/<int:appt_id>/mark-free', methods=['POST'])
@login_required
def mark_free_cut(appt_id):
    """Marcar una cita como corte gratis (solo admin y solo barberos)."""
    appt = Appointment.query.get_or_404(appt_id)
    
    # Solo funciona para citas de género masculino (barberos)
    if appt.gender != 'male':
        return jsonify({'error': 'La tarjeta de fidelidad solo aplica para servicios de barbería (hombres)'}), 400
    
    # Solo se puede marcar como gratis si está pendiente
    if appt.status != 'Pendiente':
        return jsonify({'error': 'Solo se pueden marcar como gratis las citas pendientes'}), 400
    
    # Verificar progreso en la tabla de fidelidad
    from app.models import FidelityProgress
    progress = FidelityProgress.query.filter(
        db.func.lower(FidelityProgress.client_name) == appt.client_name.lower(),
        FidelityProgress.client_phone == appt.client_phone,
        FidelityProgress.staff_name == appt.staff_name
    ).first()
    
    current_cuts = progress.current_cuts if progress else 0
    
    if current_cuts != 10:  # Debe tener exactamente 10 cortes completados (el 11 es gratis)
        return jsonify({'error': f'Cliente tiene {current_cuts} cortes, necesita 10 para el corte gratis'}), 400
    
    appt.is_free_cut = True
    appt.total = '$0'  # Marcar como gratis
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Cita marcada como corte gratis'})


@api_bp.route('/appointments/<int:appt_id>/status', methods=['PATCH'])
@login_required
def update_appointment_status(appt_id):
    """Actualizar estado de una cita (solo admin)."""
    appt = Appointment.query.get_or_404(appt_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get('status', '').strip()
    
    if new_status not in ['Pendiente', 'Completado', 'Cancelado']:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400
    if new_status == 'Completado' and appt.status != 'Completado':
        from app.models import process_fidelity_for_appointment
        process_fidelity_for_appointment(appt)
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/whatsapp/qr')
@login_required
def get_wa_qr():
    from app.whatsapp_service import get_whatsapp_qr
    return jsonify(get_whatsapp_qr())

@api_bp.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


@api_bp.route('/appointments/<int:appt_id>', methods=['DELETE'])
@login_required
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/appointments/search', methods=['GET'])
@limiter.limit("20 per minute")
def search_appointments():
    name  = _safe_str(request.args.get('name', ''), 100).lower()
    phone = _safe_str(request.args.get('phone', ''), 20)
    # Limpiar teléfono: quitar espacios, guiones y prefijo +57
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if phone.startswith('+57'):
        phone = phone[3:]
    if not name or not phone:
        return jsonify([])
    
    from datetime import date as dt_date
    today_str = dt_date.today().isoformat()
    
    # Buscar por nombre exacto (lowercase) y teléfono
    # También intentar con el teléfono con prefijo por si fue guardado así
    # Solo buscar citas pendientes cuya fecha sea hoy o en el futuro
    results = Appointment.query.filter(
        Appointment.status == 'Pendiente',
        Appointment.date >= today_str  # Solo citas de hoy en adelante
    ).filter(
        db.func.lower(Appointment.client_name) == name
    ).filter(
        db.or_(
            Appointment.client_phone == phone,
            Appointment.client_phone == '+57' + phone,
            Appointment.client_phone == '57' + phone,
        )
    ).all()
    return jsonify([_appt_dict(a) for a in results])


@api_bp.route('/appointments/taken', methods=['GET'])
def taken_slots():
    date = _safe_str(request.args.get('date', ''), 10)
    staff_name = _safe_str(request.args.get('staff', ''), 100)
    if not _valid_date(date):
        return jsonify([])
    
    from datetime import datetime
    
    # Solo buscar citas pendientes para la fecha especificada
    query = Appointment.query.filter(
        Appointment.date == date,
        Appointment.status == 'Pendiente'
    )
    if staff_name:
        query = query.filter(Appointment.staff_name == staff_name)
    appts = query.all()
    
    # Auto-completar citas que ya pasaron su hora de finalización
    now = datetime.now()
    changed = False
    for a in appts:
        try:
            h, m = map(int, a.time.split(':'))
            duration = a.duration_minutes or 60
            appt_start = datetime.strptime(f"{a.date} {a.time}", "%Y-%m-%d %H:%M")
            from datetime import timedelta
            appt_end = appt_start + timedelta(minutes=duration)
            if now >= appt_end:
                if a.status != 'Completado':
                    a.status = 'Completado'
                    from app.models import process_fidelity_for_appointment
                    process_fidelity_for_appointment(a)
                    changed = True
        except:
            pass
    
    if changed:
        db.session.commit()
        # Volver a consultar solo las citas pendientes que no han pasado
        query = Appointment.query.filter(
            Appointment.date == date,
            Appointment.status == 'Pendiente'
        )
        if staff_name:
            query = query.filter(Appointment.staff_name == staff_name)
        appts = query.all()
    
    # Calcular todos los slots bloqueados por cada cita pendiente
    blocked = set()
    for a in appts:
        h, m = map(int, a.time.split(':'))
        start_min = h * 60 + m
        dur = a.duration_minutes or 60
        # Bloquear cada slot de 15 min que ocupa esta cita
        slot = start_min
        while slot < start_min + dur:
            hh = slot // 60
            mm = slot % 60
            blocked.add(f"{hh:02d}:{mm:02d}")
            slot += 15
    return jsonify(sorted(blocked))


# ── SERVICES ──────────────────────────────────────────────────

@api_bp.route('/services', methods=['GET'])
def get_services():
    gender = request.args.get('gender', 'male')
    if gender not in ('male', 'female'):
        return jsonify([])
    services = Service.query.filter_by(gender=gender, active=True).all()
    return jsonify([_service_dict(s) for s in services])


@api_bp.route('/services', methods=['POST'])
@login_required
def create_service():
    data = request.get_json(silent=True) or {}
    dur = max(15, min(480, int(data.get('duration_minutes', 60))))
    s = Service(
        name=_safe_str(data.get('name'), 100) or 'Nuevo Servicio',
        description=_safe_str(data.get('description'), 300),
        price=max(0, int(data.get('price', 0))),
        emoji=_safe_str(data.get('emoji'), 10) or '✂',
        image_url=str(data.get('image_url') or '').strip() or None,
        duration_minutes=dur,
        gender=data.get('gender', 'male') if data.get('gender') in ('male','female') else 'male'
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(_service_dict(s)), 201


@api_bp.route('/services/<int:sid>', methods=['PUT'])
@login_required
def update_service(sid):
    s = Service.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    old_duration = s.duration_minutes
    s.name        = _safe_str(data.get('name'), 100) or s.name
    s.description = _safe_str(data.get('description'), 300)
    s.price       = max(0, int(data.get('price', s.price)))
    s.emoji       = _safe_str(data.get('emoji'), 10) or s.emoji
    new_duration  = int(data.get('duration_minutes', s.duration_minutes))
    new_duration  = max(15, min(480, new_duration))  # entre 15 min y 8 horas
    s.duration_minutes = new_duration
    img = str(data.get('image_url') or '').strip()
    if img:
        s.image_url = img
    db.session.commit()

    # Si cambió la duración, actualizar citas futuras pendientes de este servicio
    updated = 0
    if new_duration != old_duration:
        from datetime import date as dt_date
        today = dt_date.today().isoformat()
        future_appts = Appointment.query.filter(
            Appointment.service_name == s.name,
            Appointment.status == 'Pendiente',
            Appointment.date >= today
        ).all()
        for a in future_appts:
            a.duration_minutes = new_duration
            updated += 1
        db.session.commit()

    return jsonify({**_service_dict(s), 'appointments_updated': updated})


@api_bp.route('/services/<int:sid>', methods=['DELETE'])
@login_required
def delete_service(sid):
    s = Service.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})


# ── STAFF ─────────────────────────────────────────────────────

@api_bp.route('/staff', methods=['GET'])
def get_staff():
    gender = request.args.get('gender', 'male')
    if gender not in ('male', 'female'):
        return jsonify([])
    staff = Staff.query.filter_by(gender=gender, active=True).all()
    return jsonify([_staff_dict(p) for p in staff])


@api_bp.route('/staff', methods=['POST'])
@login_required
def create_staff():
    data = request.get_json(silent=True) or {}
    p = Staff(
        name=_safe_str(data.get('name'), 100) or 'Nuevo',
        title=_safe_str(data.get('title'), 100),
        experience=_safe_str(data.get('experience'), 50),
        stars=min(5, max(1, int(data.get('stars', 5)))),
        emoji=_safe_str(data.get('emoji'), 10) or '💈',
        image_url=str(data.get('image_url') or '').strip() or None,
        specialties=_safe_str(data.get('specialties'), 200),
        phone=_safe_str(data.get('phone'), 20) or None,
        instagram=_safe_str(data.get('instagram'), 100) or None,
        gender=data.get('gender', 'male') if data.get('gender') in ('male','female') else 'male'
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(_staff_dict(p)), 201


@api_bp.route('/staff/<int:pid>', methods=['PUT'])
@login_required
def update_staff(pid):
    p = Staff.query.get_or_404(pid)
    data = request.get_json(silent=True) or {}
    p.name        = _safe_str(data.get('name'), 100) or p.name
    p.title       = _safe_str(data.get('title'), 100)
    p.experience  = _safe_str(data.get('experience'), 50)
    p.stars       = min(5, max(1, int(data.get('stars', p.stars))))
    p.emoji       = _safe_str(data.get('emoji'), 10) or p.emoji
    img = str(data.get('image_url') or '').strip()
    if img:
        p.image_url = img
    p.specialties = _safe_str(data.get('specialties'), 200)
    p.phone       = _safe_str(data.get('phone'), 20) or p.phone
    p.instagram   = _safe_str(data.get('instagram'), 100) or None
    db.session.commit()
    return jsonify(_staff_dict(p))


@api_bp.route('/staff/<int:pid>', methods=['DELETE'])
@login_required
def delete_staff(pid):
    p = Staff.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'success': True})


# ── REVIEWS ───────────────────────────────────────────────────

@api_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """Reseñas públicas: solo 4-5 estrellas, máximo 15 más recientes, ordenadas por calificación y fecha."""
    # Obtener las 15 más recientes con 4+ estrellas, ordenadas por calificación (desc) y fecha (desc)
    reviews = Review.query.filter(Review.rating >= 4)\
        .order_by(Review.rating.desc(), Review.created_at.desc()).limit(15).all()
    
    # Eliminar automáticamente las reseñas antiguas que no se muestran
    # (mantener solo las 15 más recientes con 4+ estrellas)
    all_good_reviews = Review.query.filter(Review.rating >= 4)\
        .order_by(Review.rating.desc(), Review.created_at.desc()).all()
    
    if len(all_good_reviews) > 15:
        reviews_to_delete = all_good_reviews[15:]
        for r in reviews_to_delete:
            db.session.delete(r)
        db.session.commit()
    
    # Eliminar también todas las reseñas con menos de 4 estrellas
    low_reviews = Review.query.filter(Review.rating < 4).all()
    for r in low_reviews:
        db.session.delete(r)
    if low_reviews:
        db.session.commit()
    
    return jsonify([_review_dict(r) for r in reviews])

@api_bp.route('/reviews/all', methods=['GET'])
@login_required
def get_all_reviews():
    """Admin: solo las 15 más recientes con 4+ estrellas, ordenadas por calificación y fecha."""
    reviews = Review.query.filter(Review.rating >= 4)\
        .order_by(Review.rating.desc(), Review.created_at.desc()).limit(15).all()
    return jsonify([_review_dict(r) for r in reviews])

@api_bp.route('/reviews', methods=['POST'])
@limiter.limit("5 per minute")
def create_review():
    data = request.get_json(silent=True) or {}
    name    = _safe_str(data.get('client_name'), 100)
    rating  = int(data.get('rating', 0))
    comment = _safe_str(data.get('comment'), 500)
    staff   = _safe_str(data.get('staff_name'), 100)
    if not name:
        return jsonify({'success': False, 'message': 'El nombre es requerido'}), 400
    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Calificación inválida'}), 400
    r = Review(client_name=name, rating=rating, comment=comment, staff_name=staff or None)
    db.session.add(r)
    db.session.commit()
    return jsonify({'success': True, 'review': _review_dict(r)}), 201

@api_bp.route('/reviews/<int:rid>', methods=['DELETE'])
@login_required
def delete_review(rid):
    r = Review.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})

def _review_dict(r):
    return {
        'id': r.id, 'client_name': r.client_name, 'rating': r.rating,
        'comment': r.comment, 'staff_name': r.staff_name or '',
        'created_at': r.created_at.strftime('%d %b %Y') if r.created_at else ''
    }


# ── SHOP CONFIG ───────────────────────────────────────────────

_CONFIG_KEYS = {'ubicacion', 'telefono', 'wa', 'ig', 'shop_name', 'shop_logo',
                'gender_icon_male', 'gender_icon_female',
                'wa_sty', 'ig_sty', 'evo_instance'}

@api_bp.route('/config', methods=['GET'])
def get_config():
    rows = ShopConfig.query.all()
    return jsonify({r.key: r.value for r in rows})


@api_bp.route('/scheduler/status', methods=['GET'])
@login_required
def scheduler_status():
    """Admin: verificar estado del scheduler y próxima ejecución del reset semanal."""
    from app import _scheduler
    from datetime import datetime
    if _scheduler is None or not _scheduler.running:
        return jsonify({'running': False, 'message': '⚠️ Scheduler no está corriendo'})
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            'id': job.id,
            'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else 'N/A'
        })
    return jsonify({'running': True, 'jobs': jobs})

@api_bp.route('/config', methods=['POST'])
@login_required
def save_config():
    data = request.get_json(silent=True) or {}
    for key, value in data.items():
        if key not in _CONFIG_KEYS:
            continue
        row = ShopConfig.query.filter_by(key=key).first()
        if row:
            row.value = str(value or '')
        else:
            db.session.add(ShopConfig(key=key, value=str(value or '')))
    db.session.commit()
    return jsonify({'success': True})


# ── Serializers ───────────────────────────────────────────────

def _appt_dict(a):
    return {
        'id': a.id, 'name': a.client_name, 'phone': a.client_phone,
        'gender': a.gender, 'service': a.service_name, 'staff': a.staff_name,
        'date': a.date, 'time': a.time, 'total': a.total, 'status': a.status,
        'duration_minutes': a.duration_minutes, 'is_free_cut': a.is_free_cut
    }

def _service_dict(s):
    return {
        'id': s.id, 'name': s.name, 'description': s.description,
        'price': s.price, 'emoji': s.emoji, 'image_url': s.image_url,
        'gender': s.gender, 'duration_minutes': s.duration_minutes
    }

def _staff_dict(p):
    return {
        'id': p.id, 'name': p.name, 'title': p.title,
        'experience': p.experience, 'stars': p.stars,
        'emoji': p.emoji, 'image_url': p.image_url,
        'specialties': p.specialties, 'gender': p.gender,
        'phone': p.phone or '', 'instagram': p.instagram or ''
    }


# ── INACTIVE DAYS ─────────────────────────────────────────

@api_bp.route('/inactive-days', methods=['GET'])
def get_inactive_days():
    """Admin: obtener todos los días inactivos."""
    from app.models import InactiveDay
    staff_name = request.args.get('staff_name', '')
    
    query = InactiveDay.query
    if staff_name:
        query = query.filter_by(staff_name=staff_name)
    
    inactive = query.order_by(InactiveDay.date.desc()).all()
    return jsonify([{
        'id': i.id,
        'staff_name': i.staff_name,
        'date': i.date,
        'reason': i.reason,
        'created_at': i.created_at.strftime('%d %b %Y %H:%M') if i.created_at else ''
    } for i in inactive])


@api_bp.route('/inactive-days/check', methods=['GET'])
def check_staff_availability():
    """Verificar disponibilidad de un empleado en una fecha (público)."""
    from app.models import InactiveDay
    staff_name = request.args.get('staff_name', '')
    date = request.args.get('date', '')
    
    if not staff_name or not date:
        return jsonify({'available': True})
    
    inactive = InactiveDay.query.filter_by(staff_name=staff_name, date=date).first()
    return jsonify({
        'available': not bool(inactive),
        'reason': inactive.reason if inactive else '',
        'date': date,
        'staff_name': staff_name
    })


@api_bp.route('/inactive-days', methods=['POST'])
@login_required
def create_inactive_day():
    """Admin: crear un día inactivo para un empleado."""
    from app.models import InactiveDay
    from datetime import datetime, date as dt_date
    data = request.get_json(silent=True) or {}
    
    staff_name = _safe_str(data.get('staff_name'), 100)
    date = _safe_str(data.get('date'), 10)
    reason = _safe_str(data.get('reason'), 200)
    
    if not staff_name or not date:
        return jsonify({'success': False, 'message': 'Faltan campos requeridos'}), 400
    
    if not _valid_date(date):
        return jsonify({'success': False, 'message': 'Fecha inválida'}), 400
    
    # Validar que no sea una fecha pasada
    try:
        date_obj = dt_date.fromisoformat(date)
        today = dt_date.today()
        if date_obj < today:
            return jsonify({'success': False, 'message': 'No se puede marcar como inactivo una fecha pasada'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Formato de fecha inválido'}), 400
    
    # Verificar si ya existe
    existing = InactiveDay.query.filter_by(staff_name=staff_name, date=date).first()
    if existing:
        return jsonify({'success': False, 'message': 'Este día ya está marcado como inactivo'}), 409
    
    # Verificar que el empleado exista
    staff = Staff.query.filter_by(name=staff_name).first()
    if not staff:
        return jsonify({'success': False, 'message': 'El empleado no existe'}), 404
    
    # Crear el registro
    inactive = InactiveDay(staff_name=staff_name, date=date, reason=reason or '')
    db.session.add(inactive)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'✅ {staff_name} marcado como inactivo el {date}',
        'inactive_day': {
            'id': inactive.id,
            'staff_name': inactive.staff_name,
            'date': inactive.date,
            'reason': inactive.reason
        }
    }), 201


@api_bp.route('/inactive-days/<int:day_id>', methods=['DELETE'])
@login_required
def delete_inactive_day(day_id):
    """Admin: eliminar un día inactivo."""
    from app.models import InactiveDay
    
    inactive = InactiveDay.query.get_or_404(day_id)
    staff_name = inactive.staff_name
    date = inactive.date
    
    db.session.delete(inactive)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'✅ {staff_name} ya está disponible el {date}'
    })


# ── RESET DATABASE ────────────────────────────────────────────

@api_bp.route('/reset-appointments', methods=['POST'])
@login_required
def reset_appointments():
    """Admin: Reiniciar dashboard - Elimina citas completadas/canceladas, reseñas y días inactivos pasados.
    Mantiene citas pendientes y tarjetas de fidelidad."""
    try:
        from app.models import FidelityProgress, InactiveDay
        from datetime import date as dt_date
        
        # Eliminar solo citas completadas y canceladas (mantener pendientes)
        deleted_appointments = Appointment.query.filter(
            Appointment.status.in_(['Completado', 'Cancelado'])
        ).delete(synchronize_session=False)
        
        # NO eliminar tarjetas de fidelidad (se mantienen)
        fidelity_count = 0
        
        # Eliminar todas las reseñas
        review_count = Review.query.delete(synchronize_session=False)
        
        # Eliminar solo días inactivos pasados (mantener futuros)
        today_str = dt_date.today().isoformat()
        inactive_count = InactiveDay.query.filter(
            InactiveDay.date < today_str
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'✅ Dashboard reiniciado correctamente',
            'deleted': {
                'completed_cancelled_appointments': deleted_appointments,
                'fidelity_cards_kept': FidelityProgress.query.count(),
                'reviews': review_count,
                'past_inactive_days': inactive_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'❌ Error al reiniciar el dashboard: {str(e)}'
        }), 500

