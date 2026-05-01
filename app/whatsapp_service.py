import requests
import os
from datetime import datetime, timedelta

def send_whatsapp_message(to_number, message):
    """
    Envía un mensaje de WhatsApp usando UltraMsg (o similar).
    Para activarlo, debes configurar INSTANCE_ID y TOKEN en .env o ShopConfig.
    """
    # Intentar obtener de la base de datos (ShopConfig)
    from app.models import ShopConfig
    
    inst_row = ShopConfig.query.filter_by(key='ultramsg_instance').first()
    tok_row = ShopConfig.query.filter_by(key='ultramsg_token').first()
    
    instance_id = inst_row.value if inst_row and inst_row.value else os.environ.get('ULTRAMSG_INSTANCE_ID')
    token = tok_row.value if tok_row and tok_row.value else os.environ.get('ULTRAMSG_TOKEN')
    
    if not instance_id or not token or instance_id == 'YOUR_INSTANCE_ID':
        print(f"[WhatsApp] No configurado. Mensaje para {to_number}: {message[:50]}...")
        return False

    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    
    # Limpiar número: quitar espacios, signos +, guiones y paréntesis
    phone = str(to_number).strip().replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Si tiene 10 dígitos (formato celular Colombia), poner el 57 automático
    if len(phone) == 10:
        phone = '57' + phone
    # Si tiene 11 o más, asumimos que ya trae el código de país o es internacional
        
    payload = {
        "token": token,
        "to": phone,
        "body": message
    }
    
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"[WhatsApp] Respuesta de API: {response.text}")
        return response.json().get('sent') == 'true'
    except Exception as e:
        print(f"[WhatsApp] Error enviando mensaje: {e}")
        return False

def notify_admin_new_appointment(appt, shop_name):
    """Notifica al barbero o estilista específico de una nueva cita."""
    msg = (
        f"🚨 *NUEVA RESERVACIÓN* 💈\n\n"
        f"👤 *Cliente:* {appt.client_name}\n"
        f"✂️ *Servicio:* {appt.service_name}\n"
        f"📅 *Fecha:* {appt.date}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"💰 *Total:* {appt.total}\n\n"
        f"Te han agendado una cita."
    )
    
    # 1. Intentar enviar al teléfono del barbero/estilista específico
    from app.models import Staff, ShopConfig
    to = None
    staff = Staff.query.filter_by(name=appt.staff_name).first()
    
    if staff and staff.phone:
        to = staff.phone
        print(f"[WhatsApp] Notificando directamente a {staff.name} al {to}")
    else:
        # 2. Si no tiene teléfono, enviar al número principal de la tienda
        admin_wa = ShopConfig.query.filter_by(key='wa').first()
        to = admin_wa.value if admin_wa and admin_wa.value else os.environ.get('ADMIN_PHONE')
        print(f"[WhatsApp] Barbero sin teléfono, notificando a la tienda: {to}")
    
    if to:
        send_whatsapp_message(to, msg)

def send_reminder_to_client(appt, shop_name):
    """Envía un recordatorio al cliente 20 minutos antes."""
    msg = (
        f"⏰ *RECORDATORIO DE CITA* 💈\n\n"
        f"Hola *{appt.client_name}*, te recordamos tu cita en *{shop_name}* en 20 minutos.\n\n"
        f"📍 *Servicio:* {appt.service_name}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"👤 *Te atiende:* {appt.staff_name}\n\n"
        f"¡Te esperamos!"
    )
    send_whatsapp_message(appt.client_phone, msg)
