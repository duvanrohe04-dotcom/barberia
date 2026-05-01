import requests
import os
from datetime import datetime, timedelta

EVOLUTION_BASE_URL = os.environ.get('EVOLUTION_API_URL', 'http://evolution_api:8080')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'barberking_secret_key')

def send_whatsapp_message(to_number, message):
    from app.models import ShopConfig
    
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else 'barberking'
    
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
    from app.models import ShopConfig
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else 'barberking'
    clean_name = instance_name.strip().lower()

    base_url = EVOLUTION_BASE_URL
    api_key = EVOLUTION_API_KEY
    
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        check_res = requests.get(f"{base_url}/instance/fetchInstances", headers=headers, timeout=10)
        exists = False
        if check_res.status_code == 200:
            try: 
                res_data = check_res.json()
                instances = res_data if isinstance(res_data, list) else res_data.get('instances', [])
                if any(inst.get('instanceName') == clean_name for inst in instances):
                    exists = True
            except: 
                exists = False
            
        if not exists:
            print(f"[WA] Creando instancia '{clean_name}'...")
            payload = {
                "instanceName": clean_name,
                "token": api_key,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            create_res = requests.post(f"{base_url}/instance/create", json=payload, headers=headers, timeout=15)
             
            if create_res.status_code not in [200, 201, 403, 409]:
                return {"success": False, "message": f"Error al crear: {create_res.text[:100]}"}
                 
            import time
            time.sleep(3)
  
    except Exception as e:
        print(f"[WA] Error en pre-vuelo: {e}")
  
    qr_url = f"{base_url}/instance/connect/{clean_name}"
    try:
        res = requests.get(qr_url, headers=headers, timeout=25)
        
        if res.status_code == 404:
            return {"success": False, "message": f"Instancia '{clean_name}' no encontrada."}
        
        if res.status_code != 200:
            return {"success": False, "message": f"Error {res.status_code}: {res.text[:100]}"}
             
        return res.json()
              
    except Exception as e:
        return {"success": False, "message": f"Fallo de red: {str(e)}"}

def notify_admin_new_appointment(appt, shop_name):
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
    msg = (
        f"⏰ *RECORDATORIO DE CITA* 💈\n\n"
        f"Hola *{appt.client_name}*, te recordamos tu cita en *{shop_name}* en 20 minutos.\n\n"
        f"📍 *Servicio:* {appt.service_name}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"👤 *Te atiende:* {appt.staff_name}\n\n"
        f"¡Te esperamos!"
    )
    send_whatsapp_message(appt.client_phone, msg)
