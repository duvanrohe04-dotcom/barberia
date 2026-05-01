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
    
    print(f"[WA] Intentando conectar instancia: {clean_name}")
    print(f"[WA] URL base: {base_url}")
    
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Verificar si la instancia existe
        check_res = requests.get(f"{base_url}/instance/fetchInstances", headers=headers, timeout=10)
        exists = False
        
        if check_res.status_code == 200:
            try: 
                res_data = check_res.json()
                instances = res_data if isinstance(res_data, list) else res_data.get('instances', [])
                
                for inst in instances:
                    if inst.get('instanceName') == clean_name or inst.get('instance', {}).get('instanceName') == clean_name:
                        exists = True
                        # Verificar si ya está conectada
                        state = inst.get('state') or inst.get('instance', {}).get('state')
                        if state == 'open':
                            print(f"[WA] Instancia ya conectada")
                            return {"success": True, "instance": {"state": "open"}, "message": "WhatsApp ya está conectado"}
                        break
                        
                print(f"[WA] Instancia existe: {exists}")
            except Exception as e: 
                print(f"[WA] Error parseando instancias: {e}")
                exists = False
            
        # Si no existe, crearla
        if not exists:
            print(f"[WA] Creando instancia '{clean_name}'...")
            payload = {
                "instanceName": clean_name,
                "token": api_key,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            create_res = requests.post(f"{base_url}/instance/create", json=payload, headers=headers, timeout=15)
            
            print(f"[WA] Respuesta crear instancia: {create_res.status_code} - {create_res.text[:200]}")
             
            if create_res.status_code not in [200, 201, 403, 409]:
                return {"success": False, "message": f"Error al crear instancia: {create_res.text[:100]}"}
                 
            import time
            time.sleep(3)
  
    except Exception as e:
        print(f"[WA] Error en verificación de instancia: {e}")
        return {"success": False, "message": f"Error de conexión: {str(e)}"}
  
    # Obtener el QR
    qr_url = f"{base_url}/instance/connect/{clean_name}"
    print(f"[WA] Solicitando QR desde: {qr_url}")
    
    try:
        res = requests.get(qr_url, headers=headers, timeout=25)
        
        print(f"[WA] Respuesta QR: {res.status_code}")
        print(f"[WA] Contenido: {res.text[:500]}")
        
        if res.status_code == 404:
            return {"success": False, "message": f"Instancia '{clean_name}' no encontrada. Verifica la configuración."}
        
        if res.status_code != 200:
            return {"success": False, "message": f"Error {res.status_code}: {res.text[:100]}"}
        
        data = res.json()
        
        # Evolution API puede devolver diferentes formatos
        # Formato 1: {"base64": "data:image/png;base64,..."}
        # Formato 2: {"qrcode": {"base64": "..."}}
        # Formato 3: {"code": "...", "base64": "..."}
        
        if 'base64' in data:
            return {"success": True, "base64": data['base64']}
        elif 'qrcode' in data and isinstance(data['qrcode'], dict) and 'base64' in data['qrcode']:
            return {"success": True, "base64": data['qrcode']['base64']}
        elif 'code' in data:
            # Si viene el código del QR, generar la imagen
            import qrcode
            import io
            import base64
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data['code'])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return {"success": True, "base64": f"data:image/png;base64,{img_str}"}
        else:
            print(f"[WA] Formato de respuesta no reconocido: {data}")
            return {"success": False, "message": "Formato de respuesta no reconocido. Verifica la configuración de Evolution API."}
              
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Tiempo de espera agotado. El servidor de WhatsApp no responde."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "No se puede conectar al servidor de WhatsApp. Verifica que Evolution API esté corriendo."}
    except Exception as e:
        print(f"[WA] Error obteniendo QR: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

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
