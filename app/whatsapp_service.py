import requests
import os
import time
import qrcode
import io
import base64
from datetime import datetime, timedelta

EVOLUTION_BASE_URL = os.environ.get('EVOLUTION_API_URL', 'http://evolution_api:8080')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'barberking_secret_key')
DEFAULT_INSTANCE = os.environ.get('DEFAULT_INSTANCE', 'barberking')

def send_whatsapp_message(to_number, message):
    from app.models import ShopConfig
    
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else DEFAULT_INSTANCE
    
    # Limpiar y formatear el número
    phone = str(to_number).strip().replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '')
    
    print(f"[WhatsApp] Número original: {to_number}")
    print(f"[WhatsApp] Número limpio: {phone}")
    
    # Si es un número de 10 dígitos (Colombia), agregar código de país
    # Validar que no empiece ya con 57
    if len(phone) == 10 and not phone.startswith('57'):
        phone = '57' + phone
        print(f"[WhatsApp] Agregado código de país: {phone}")
    elif len(phone) == 12 and phone.startswith('57'):
        print(f"[WhatsApp] Número ya tiene código de país: {phone}")
    else:
        print(f"[WhatsApp] ⚠️ Formato de número inusual: longitud={len(phone)}, valor={phone}")
    
    # Evolution API requiere el formato: número@s.whatsapp.net
    if not phone.endswith('@s.whatsapp.net'):
        phone = phone + '@s.whatsapp.net'
    
    url = f"{EVOLUTION_BASE_URL}/message/sendText/{instance_name}"
    
    print(f"[WhatsApp] Enviando mensaje a: {phone}")
    print(f"[WhatsApp] Instancia: {instance_name}")
    print(f"[WhatsApp] URL: {url}")
    
    headers = {
        'Content-Type': 'application/json',
        'apikey': EVOLUTION_API_KEY
    }
    
    # Evolution API v2.x requiere el formato simplificado
    payload = {
        "number": phone,
        "text": message,
        "options": {
            "delay": 1200,
            "presence": "composing"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[WhatsApp] Status: {response.status_code}")
        print(f"[WhatsApp] Respuesta: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            try:
                resp_json = response.json()
                if resp_json.get('error') or resp_json.get('status') == 'error':
                    print(f"[WhatsApp] ❌ API devolvió error: {resp_json}")
                    return False
                print(f"[WhatsApp] ✅ Mensaje enviado exitosamente")
            except:
                pass
            return True
        else:
            print(f"[WhatsApp] ❌ Error al enviar mensaje: {response.text[:300]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[WhatsApp] ❌ Timeout al enviar mensaje")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[WhatsApp] ❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"[WhatsApp] ❌ Error enviando mensaje: {e}")
        return False

def get_whatsapp_qr():
    from app.models import ShopConfig
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else DEFAULT_INSTANCE
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
                
                print(f"[WA] Instancias encontradas: {[i.get('instanceName', i.get('instance', {}).get('instanceName', 'unknown')) for i in instances]}")
                
                for inst in instances:
                    inst_name = inst.get('instanceName') or inst.get('instance', {}).get('instanceName', '')
                    if inst_name == clean_name:
                        exists = True
                        # Verificar estado de conexión
                        state = inst.get('state') or inst.get('instance', {}).get('state')
                        print(f"[WA] Instancia '{clean_name}' encontrada, estado: {state}")
                        
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
        
        print(f"[WA] Datos recibidos del QR: {list(data.keys())}")
        
        # Evolution API v2.3.7 puede devolver diferentes formatos:
        # Formato 1: {"base64": "data:image/png;base64,..."}
        # Formato 2: {"code": "...", "base64": "data:image/png;base64,..."}
        # Formato 3: {"instance": {"instanceName": "...", "state": "connecting"}, "code": "...", "base64": "..."}
        # Formato 4: {"qrcode": {"base64": "..."}}
        
        # Caso 1: ya está conectado
        if 'instance' in data and data.get('instance', {}).get('state') == 'open':
            return {"success": True, "instance": {"state": "open"}, "message": "WhatsApp ya está conectado"}
        
        # Caso 2: viene base64 directo
        if 'base64' in data:
            b64 = data['base64']
            if b64 and len(b64) > 50:
                if not b64.startswith('data:'):
                    b64 = f"data:image/png;base64,{b64}"
                return {"success": True, "base64": b64}
        
        # Caso 3: viene dentro de qrcode object
        if 'qrcode' in data and isinstance(data['qrcode'], dict):
            b64 = data['qrcode'].get('base64', '')
            if b64 and len(b64) > 50:
                if not b64.startswith('data:'):
                    b64 = f"data:image/png;base64,{b64}"
                return {"success": True, "base64": b64}
        
        # Caso 4: viene solo el code (generar QR manualmente)
        if 'code' in data and data['code']:
            print(f"[WA] Generando QR manualmente desde code")
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data['code'])
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return {"success": True, "base64": f"data:image/png;base64,{img_str}"}
        
        # Caso 5: instancia en estado connecting/close pero sin QR todavía
        if 'instance' in data:
            state = data['instance'].get('state', 'desconocido')
            print(f"[WA] Instancia en estado '{state}', sin QR disponible aún")
            return {"success": False, "message": f"Instancia en estado '{state}'. Espera unos segundos e intenta de nuevo."}
        
        # Si nada funcionó, imprimir debug y devolver error
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
    """Envía notificación de nueva cita al empleado o admin."""
    print(f"[WhatsApp] ========================================")
    print(f"[WhatsApp] Iniciando notificación de nueva cita")
    print(f"[WhatsApp] Cliente: {appt.client_name}")
    print(f"[WhatsApp] Empleado: {appt.staff_name}")
    print(f"[WhatsApp] Servicio: {appt.service_name}")
    print(f"[WhatsApp] Fecha: {appt.date} - Hora: {appt.time}")
    
    # Formatear el total correctamente
    try:
        total_formatted = f"${float(appt.total.replace('$', '').replace(',', '')):,.0f}" if appt.total else "$0"
    except:
        total_formatted = appt.total or "$0"
    
    print(f"[WhatsApp] Total formateado: {total_formatted}")
    
    msg = (
        f"🚨 *NUEVA RESERVACIÓN* 💈\n\n"
        f"👤 *Cliente:* {appt.client_name}\n"
        f"📞 *Teléfono:* {appt.client_phone}\n"
        f"✂️ *Servicio:* {appt.service_name}\n"
        f"📅 *Fecha:* {appt.date}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"💰 *Total:* {total_formatted}\n\n"
        f"Te han agendado una cita en *{shop_name}*."
    )
    
    print(f"[WhatsApp] Mensaje preparado (primeros 100 chars): {msg[:100]}")
    
    from app.models import Staff, ShopConfig
    to = None
    staff = Staff.query.filter_by(name=appt.staff_name).first()
    
    if staff:
        print(f"[WhatsApp] Empleado encontrado en BD: {staff.name}")
        print(f"[WhatsApp] Teléfono del empleado: {staff.phone if staff.phone else 'NO CONFIGURADO'}")
    else:
        print(f"[WhatsApp] ⚠️ Empleado NO encontrado en BD: {appt.staff_name}")
    
    if staff and staff.phone:
        to = staff.phone
        print(f"[WhatsApp] ✅ Enviando a empleado: {staff.name} - {to}")
    else:
        admin_wa = ShopConfig.query.filter_by(key='wa').first()
        to = admin_wa.value if admin_wa and admin_wa.value else os.environ.get('ADMIN_PHONE')
        print(f"[WhatsApp] ⚠️ Empleado sin teléfono, enviando a admin: {to}")
    
    if to:
        print(f"[WhatsApp] Número destino final: {to}")
        result = send_whatsapp_message(to, msg)
        if result:
            print(f"[WhatsApp] ✅ Notificación enviada exitosamente")
        else:
            print(f"[WhatsApp] ❌ Falló el envío de notificación")
        print(f"[WhatsApp] ========================================")
        return result
    else:
        print(f"[WhatsApp] ❌ No hay número de teléfono configurado")
        print(f"[WhatsApp] ========================================")
        return False

def send_reminder_to_client(appt, shop_name):
    """Envía recordatorio de cita al cliente 20 minutos antes."""
    print(f"[WhatsApp] Enviando recordatorio a cliente: {appt.client_name}")
    
    msg = (
        f"⏰ *RECORDATORIO DE CITA* 💈\n\n"
        f"Hola *{appt.client_name}*, te recordamos tu cita en *{shop_name}* en 20 minutos.\n\n"
        f"📍 *Servicio:* {appt.service_name}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"👤 *Te atiende:* {appt.staff_name}\n\n"
        f"¡Te esperamos!"
    )
    
    result = send_whatsapp_message(appt.client_phone, msg)
    
    if result:
        print(f"[WhatsApp] ✅ Recordatorio enviado a {appt.client_name}")
    else:
        print(f"[WhatsApp] ❌ Falló el envío de recordatorio a {appt.client_name}")
    
    return result
