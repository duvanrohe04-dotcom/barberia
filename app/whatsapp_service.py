import requests
import os
from datetime import datetime, timedelta

# URL interna de Docker para hablar con el servicio Evolution API
# Si estás en local fuera de docker, cambia esto a 'http://localhost:8080'
EVOLUTION_BASE_URL = os.environ.get('EVOLUTION_API_URL', 'http://evolution_api:8080')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'barberking_secret_key')

def send_whatsapp_message(to_number, message):
    """
    Envía un mensaje de WhatsApp usando Evolution API (Self-hosted).
    """
    from app.models import ShopConfig
    
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else 'barberking'
    
    # Limpiar número: quitar espacios, signos +, etc.
    phone = str(to_number).strip().replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '')
    if len(phone) == 10:
        phone = '57' + phone

    url = f"{EVOLUTION_BASE_URL}/message/sendText/{instance_name}"
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    payload = {
        "number": phone,
        "options": {
            "delay": 1200,
            "presence": "composing",
            "linkPreview": False
        },
        "textMessage": {
            "text": message
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[WhatsApp] Respuesta Evolution: {response.text}")
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"[WhatsApp] Error enviando mensaje via Evolution: {e}")
        return False

def get_whatsapp_qr():
    """Obtiene el QR o el estado de la conexión."""
    from app.models import ShopConfig
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else 'barberking'

    # Valores forzados para máxima estabilidad
    BASE_URL = "http://evolution_api:8080"
    API_KEY = "barberking_secret_key"
    
    # 1. Crear instancia (si no existe)
    create_url = f"{BASE_URL}/instance/create"
    headers = {
        'apikey': API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        # Formato simplificado al máximo para v2
        payload = {"instanceName": instance_name}
        r = requests.post(create_url, json=payload, headers=headers, timeout=10)
        print(f"[WA] Intento crear instancia '{instance_name}': {r.status_code}")
        
        import time
        time.sleep(2)
        
    except Exception as e:
        print(f"[WA] Error creando instancia: {e}")

    # 2. Conectar / Obtener QR
    qr_url = f"{BASE_URL}/instance/connect/{instance_name}"
    try:
        res = requests.get(qr_url, headers=headers, timeout=20)
        
        if res.status_code == 404:
            return {"success": False, "message": f"Error 404: El motor no reconoce la instancia '{instance_name}'. Respuesta: {res.text[:30]}"}
        
        if res.status_code != 200:
            return {"success": False, "message": f"Error {res.status_code} al conectar con WhatsApp."}
            
        try:
            return res.json()
        except:
            return {"success": False, "message": "Respuesta no válida del servidor de WhatsApp."}
            
    except Exception as e:
        return {"success": False, "message": f"Error de red: {str(e)}"}

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
    
    from app.models import Staff, ShopConfig
    to = None
    staff = Staff.query.filter_by(name=appt.staff_name).first()
    
    if staff and staff.phone:
        to = staff.phone
    else:
        admin_wa = ShopConfig.query.filter_by(key='wa').first()
        to = admin_wa.value if admin_wa and admin_wa.value else os.environ.get('ADMIN_PHONE')
    
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
