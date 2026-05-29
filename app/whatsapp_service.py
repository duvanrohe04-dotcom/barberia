import json
import os
import sys
import time
import qrcode
import io
import base64
import urllib.request
import urllib.error
import socket
from urllib.parse import urlparse
from datetime import datetime, timedelta

is_local_runtime = sys.platform == 'win32' or os.environ.get('FLASK_ENV') == 'development'

# Cache para evitar resolver DNS en cada llamada
_evolution_url_cache = None


def _resolve_evolution_base_url():
    global _evolution_url_cache
    if _evolution_url_cache is not None:
        return _evolution_url_cache

    env_url = (os.environ.get('EVOLUTION_API_URL') or '').strip()
    server_url = (os.environ.get('EVOLUTION_SERVER_URL') or '').strip()

    if env_url:
        if env_url.startswith(('http://', 'https://')):
            if is_local_runtime:
                parsed = urlparse(env_url)
                try:
                    socket.getaddrinfo(parsed.hostname, parsed.port or 8080)
                except Exception:
                    print(f"[WA] ⚠️ Host '{parsed.hostname}' no alcanzable desde entorno local.")
                    print(f"[WA] Ignorando EVOLUTION_API_URL y buscando alternativa...")
                    env_url = None
            if env_url:
                _evolution_url_cache = env_url
                return env_url
        else:
            print(f"[WA] ⚠️ EVOLUTION_API_URL tiene un valor inválido: '{env_url[:50]}...'")
            print(f"[WA] Intentando auto-detectar...")

    # Posibles nombres para Evolution API en Coolify / Docker
    candidates = [
        'http://evolution-api:8080',
        'http://evolution_api:8080',
        'http://evolutionapi:8080',
        'http://evolution:8080',
        'http://whatsapp-api:8080',
        'http://whatsapp_api:8080',
    ]

    # También probar EVOLUTION_SERVER_URL como candidato
    if server_url and server_url.startswith(('http://', 'https://')):
        candidates.insert(0, server_url)

    for candidate in candidates:
        parsed = urlparse(candidate)
        try:
            socket.getaddrinfo(parsed.hostname, parsed.port or 8080)
            print(f"[WA] Evolution API detectado en: {candidate}")
            _evolution_url_cache = candidate
            return candidate
        except Exception:
            continue

    # Fallback
    if sys.platform == 'win32' or os.environ.get('FLASK_ENV') == 'development':
        # Intentar server_url primero (que suele tener el puerto externo correcto)
        if server_url and server_url.startswith(('http://', 'https://')):
            print(f"[WA] Usando EVOLUTION_SERVER_URL como fallback local: {server_url}")
            _evolution_url_cache = server_url
            return _evolution_url_cache
        print("[WA] Usando 127.0.0.1:8085 como fallback local.")
        _evolution_url_cache = 'http://127.0.0.1:8085'
        return _evolution_url_cache

    fallback = env_url or 'http://evolution-api:8080'
    print(f"[WA] Usando fallback: {fallback}")
    print("[WA] Si no funciona, configura EVOLUTION_API_URL en Coolify.")
    _evolution_url_cache = fallback
    return fallback


def get_evolution_base_url():
    return _resolve_evolution_base_url()


EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY')
if not EVOLUTION_API_KEY:
    raise RuntimeError('EVOLUTION_API_KEY environment variable is required')
DEFAULT_INSTANCE = os.environ.get('DEFAULT_INSTANCE', 'barberking')

# Mantener EVOLUTION_BASE_URL para compatibilidad
EVOLUTION_BASE_URL = _resolve_evolution_base_url()


def _http_request(method, url, payload=None, headers=None, timeout=15):
    data = None
    req_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        req_headers.setdefault('Content-Type', 'application/json')

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode('utf-8', errors='ignore')
            try:
                parsed = json.loads(body) if body else None
            except ValueError:
                parsed = None
            return response.status, body, parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='ignore')
        try:
            parsed = json.loads(body) if body else None
        except ValueError:
            parsed = None
        return exc.code, body, parsed
    except urllib.error.URLError as exc:
        raise ConnectionError(str(exc.reason)) from exc
    except TimeoutError as exc:
        raise TimeoutError('Tiempo de espera agotado') from exc


def send_whatsapp_message(to_number, message):
    from app.models import ShopConfig
    base_url = None
    
    try:
        inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
        instance_name = inst_row.value if inst_row and inst_row.value else DEFAULT_INSTANCE
        
        # Limpiar y formatear el número
        phone = str(to_number).strip().replace(' ', '').replace('+', '').replace('-', '').replace('(', '').replace(')', '')
        
        print(f"[WhatsApp] Número original: {to_number}")
        print(f"[WhatsApp] Número limpio: {phone}")
        
        # Si es un número de 10 dígitos (Colombia), agregar código de país
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
        
        base_url = get_evolution_base_url()
        url = f"{base_url}/message/sendText/{instance_name}"
        
        print(f"[WhatsApp] Enviando mensaje a: {phone}")
        print(f"[WhatsApp] Instancia: {instance_name}")
        print(f"[WhatsApp] URL base: {base_url}")
        print(f"[WhatsApp] URL completa: {url}")
        
        headers = {
            'Content-Type': 'application/json',
            'apikey': EVOLUTION_API_KEY
        }
        
        payload = {
            "number": phone,
            "text": message,
            "delay": 1200,
            "presence": "composing"
        }
        
        try:
            status, body, resp_json = _http_request('POST', url, payload=payload, headers=headers, timeout=15)
            print(f"[WhatsApp] Status: {status}")
            print(f"[WhatsApp] Respuesta: {body[:500] if body else 'Sin respuesta'}")

            if status in [200, 201]:
                if isinstance(resp_json, dict) and (resp_json.get('error') or resp_json.get('status') == 'error'):
                    print(f"[WhatsApp] ❌ API devolvió error: {resp_json}")
                    return False, resp_json.get('error', str(resp_json))
                print(f"[WhatsApp] ✅ Mensaje enviado exitosamente")
                return True, None

            error_detail = body[:300] if body else f"HTTP {status}"
            print(f"[WhatsApp] ❌ Error al enviar mensaje: {error_detail}")
            return False, error_detail

        except TimeoutError:
            msg = f"Tiempo de espera agotado. Evolution API en {base_url or 'servidor'} no responde."
            print(f"[WhatsApp] ❌ {msg}")
            return False, msg
        except ConnectionError as e:
            msg = f"No se puede conectar a Evolution API en {base_url or 'servidor'}: {e}"
            print(f"[WhatsApp] ❌ {msg}")
            return False, msg

    except Exception as e:
        msg = str(e)
        print(f"[WhatsApp] ❌ Error enviando mensaje: {e}")
        import traceback
        traceback.print_exc()
        return False, msg

def disconnect_whatsapp():
    """Desconecta la instancia de WhatsApp usando Evolution API v2."""
    base_url = None
    instance_name = None
    try:
        print(f"[WA] Iniciando desconexión...")

        from app.models import ShopConfig

        inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
        instance_name = inst_row.value if inst_row and inst_row.value else DEFAULT_INSTANCE
        base_url = get_evolution_base_url()
        api_key = EVOLUTION_API_KEY
        
        print(f"[WA] Instancia: {instance_name}")
        print(f"[WA] URL base: {base_url}")

        reachable = _check_evolution_reachable()
        if reachable:
            return {'success': False, 'message': reachable}
        
        headers = {'apikey': api_key}
        url = f"{base_url}/instance/logout/{instance_name}"
        print(f"[WA] DELETE to: {url}")
        
        status, body, _ = _http_request('DELETE', url, headers=headers, timeout=5)
        print(f"[WA] Status: {status}")
        print(f"[WA] Response: {body[:200] if body else 'Sin respuesta'}")

        if status == 200:
            return {'success': True, 'message': 'WhatsApp desconectado exitosamente.'}
        if status == 404:
            return {'success': True, 'message': 'Instancia no encontrada (posiblemente ya desconectada).'}
        return {'success': False, 'message': f'Error {status}: {body[:100] if body else "Sin respuesta"}'}

    except TimeoutError:
        url_str = base_url or 'servidor'
        print(f"[WA] TIMEOUT: No se pudo conectar a Evolution API en {url_str}")
        try:
            msg = _check_evolution_reachable()
        except Exception as check_err:
            print(f"[WA] Error en _check_evolution_reachable: {check_err}")
            msg = None
        return {'success': False, 'message': msg or 'Tiempo agotado. No se puede conectar a Evolution API.'}
    except ConnectionError as conn_err:
        url_str = base_url or 'servidor'
        print(f"[WA] CONNECTION ERROR: No se puede conectar a {url_str}: {conn_err}")
        try:
            msg = _check_evolution_reachable()
        except Exception as check_err:
            print(f"[WA] Error en _check_evolution_reachable: {check_err}")
            msg = None
        return {'success': False, 'message': msg or 'Error de conexión. Evolution API no disponible.'}
    except Exception as e:
        print(f"[WA] EXCEPCIÓN: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': f'Error: {str(e)}'}

def _check_evolution_reachable():
    """Verifica si el host de Evolution API es alcanzable. Retorna mensaje de error o None."""
    base_url = get_evolution_base_url()
    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or 8080
    try:
        socket.getaddrinfo(host, port)
        return None
    except Exception as e:
        error_msg = str(e).lower()
        if 'name' in error_msg or 'resolution' in error_msg or 'temporary' in error_msg:
            return (f"❌ No se puede resolver el host '{host}'. "
                    f"Evolution API no está corriendo o la URL es incorrecta.\n"
                    f"URL actual: {base_url}\n\n"
                    f"💡 Solución: Configura EVOLUTION_API_URL en las variables "
                    f"de entorno de Coolify con la URL correcta de tu Evolution API.")
        return f"❌ No se puede conectar a Evolution API en {base_url}: {e}"


def get_whatsapp_qr():
    from app.models import ShopConfig
    inst_row = ShopConfig.query.filter_by(key='evo_instance').first()
    instance_name = inst_row.value if inst_row and inst_row.value else DEFAULT_INSTANCE
    clean_name = instance_name.strip().lower()

    base_url = get_evolution_base_url()
    api_key = EVOLUTION_API_KEY
    
    print(f"[WA] Intentando conectar instancia: {clean_name}")
    print(f"[WA] URL base: {base_url}")

    reachable = _check_evolution_reachable()
    if reachable:
        print(f"[WA] Host NO alcanzable: {reachable}")
        return {"success": False, "message": reachable}
    
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Verificar si la instancia existe
        status, body, res_data = _http_request('GET', f"{base_url}/instance/fetchInstances", headers=headers, timeout=10)
        exists = False

        if status == 200:
            try:
                if res_data is None:
                    res_data = json.loads(body) if body else {}
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
            status, body, _ = _http_request('POST', f"{base_url}/instance/create", payload=payload, headers=headers, timeout=15)

            print(f"[WA] Respuesta crear instancia: {status} - {body[:200]}")

            if status not in [200, 201, 403, 409]:
                return {"success": False, "message": f"Error al crear instancia: {body[:100]}"}
             
            time.sleep(3)
  
    except Exception as e:
        print(f"[WA] Error en verificación de instancia: {e}")
        reachable = _check_evolution_reachable()
        if reachable:
            return {"success": False, "message": reachable}
        return {"success": False, "message": f"Error de conexión: {str(e)}"}
  
    # Obtener el QR (reintentar hasta que esté disponible)
    qr_url = f"{base_url}/instance/connect/{clean_name}"
    print(f"[WA] Solicitando QR desde: {qr_url}")

    max_attempts = 8
    for attempt in range(1, max_attempts + 1):
        try:
            status, body, data = _http_request('GET', qr_url, headers=headers, timeout=20)

            print(f"[WA] Intento {attempt}/{max_attempts} - Status: {status}")
            print(f"[WA] Contenido: {body[:500]}")

            if status == 404:
                return {"success": False, "message": f"Instancia '{clean_name}' no encontrada. Verifica la configuración."}

            if status != 200:
                return {"success": False, "message": f"Error {status}: {body[:100]}"}

            if data is None:
                data = json.loads(body) if body else {}

            print(f"[WA] Datos recibidos: {list(data.keys())}")

            # Normalizar: aplanar qrcode{} si existe para no buscar en dos niveles
            if isinstance(data.get('qrcode'), dict):
                for k, v in data['qrcode'].items():
                    if k not in data or data[k] is None:
                        data[k] = v

            qr_count = data.get('count', 0)
            b64 = data.get('base64', '') or ''
            code = data.get('code') or data.get('pairingCode') or ''
            inst_state = data.get('instance', {}).get('state') or data.get('instance', {}).get('connectionStatus', '')

            print(f"[WA] count={qr_count}, base64={'si' if b64 and len(b64)>50 else 'no'}, code={'si' if code else 'no'}, state={inst_state}")

            # count = 0 y sin datos de QR → reintentar
            if qr_count == 0 and not (b64 and len(b64) > 50) and not code:
                if attempt < max_attempts:
                    print(f"[WA] QR no disponible (count={qr_count}), reintentando en 3s...")
                    time.sleep(3)
                    continue
                return {"success": False, "message": "⏳ El código QR aún no se ha generado. Espera unos segundos e intenta de nuevo."}

            # Ya conectado
            if inst_state in ('open', 'CONNECTED'):
                return {"success": True, "instance": {"state": "open"}, "message": "WhatsApp ya está conectado"}

            # base64 directo
            if b64 and len(b64) > 50:
                if not b64.startswith('data:'):
                    b64 = f"data:image/png;base64,{b64}"
                return {"success": True, "base64": b64}

            # code → generar QR manualmente
            if code:
                print(f"[WA] Generando QR desde code/pairingCode")
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(code)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode()
                return {"success": True, "base64": f"data:image/png;base64,{img_str}"}

            # Sin QR y sin estar conectado
            print(f"[WA] Formato no reconocido: {data}")
            return {"success": False, "message": f"QR no disponible (estado: {inst_state}). Espera unos segundos e intenta de nuevo."}
        except TimeoutError:
            return {"success": False, "message": "Tiempo de espera agotado. El servidor de WhatsApp no responde."}
        except ConnectionError:
            return {"success": False, "message": "No se puede conectar al servidor de WhatsApp. Verifica que Evolution API esté corriendo."}
        except Exception as e:
            print(f"[WA] Error obteniendo QR: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}

def notify_staff_cancelled(appt, shop_name):
    """Envía notificación al barbero/estilista cuando el cliente cancela una cita."""
    print(f"[WhatsApp] ========================================")
    print(f"[WhatsApp] Iniciando notificación de cancelación al empleado")
    print(f"[WhatsApp] Cliente: {appt.client_name}")
    print(f"[WhatsApp] Empleado: {appt.staff_name}")
    print(f"[WhatsApp] Servicio: {appt.service_name}")
    print(f"[WhatsApp] Fecha: {appt.date} - Hora: {appt.time}")
    
    try:
        total_formatted = f"${float(appt.total.replace('$', '').replace(',', '')):,.0f}" if appt.total else "$0"
    except:
        total_formatted = appt.total or "$0"
    
    msg = (
        f"❌ *CITA CANCELADA POR EL CLIENTE* 💈\n\n"
        f"👤 *Cliente:* {appt.client_name}\n"
        f"📞 *Teléfono:* {appt.client_phone}\n"
        f"✂️ *Servicio:* {appt.service_name}\n"
        f"📅 *Fecha:* {appt.date}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"💰 *Valor:* {total_formatted}\n\n"
        f"El cliente canceló su cita en *{shop_name}*."
    )
    
    from app.models import Staff, ShopConfig
    to = None
    staff = Staff.query.filter_by(name=appt.staff_name).first()
    
    if staff and staff.phone:
        to = staff.phone
        print(f"[WhatsApp] ✅ Enviando notificación al empleado: {staff.name} - {to}")
    else:
        admin_wa = ShopConfig.query.filter_by(key='wa').first()
        to = admin_wa.value if admin_wa and admin_wa.value else None
        print(f"[WhatsApp] ⚠️ Empleado sin teléfono, enviando a admin: {to}")
    
    if to:
        success, error = send_whatsapp_message(to, msg)
        if success:
            print(f"[WhatsApp] ✅ Notificación de cancelación enviada al empleado")
        else:
            print(f"[WhatsApp] ❌ Falló el envío de notificación de cancelación: {error}")
        print(f"[WhatsApp] ========================================")
        return success
    else:
        print(f"[WhatsApp] ❌ No hay número de teléfono configurado")
        print(f"[WhatsApp] ========================================")
        return False

def notify_client_cancelled(appt, shop_name):
    """Envía notificación al cliente cuando el administrador cancela su cita."""
    print(f"[WhatsApp] ========================================")
    print(f"[WhatsApp] Iniciando notificación de cancelación al cliente")
    print(f"[WhatsApp] Cliente: {appt.client_name}")
    print(f"[WhatsApp] Teléfono: {appt.client_phone}")
    
    try:
        total_formatted = f"${float(appt.total.replace('$', '').replace(',', '')):,.0f}" if appt.total else "$0"
    except:
        total_formatted = appt.total or "$0"
    
    msg = (
        f"❌ *CITA CANCELADA POR LA BARBERÍA* 💈\n\n"
        f"Hola *{appt.client_name}*, te informamos que tu cita ha sido cancelada por la barbería.\n\n"
        f"✂️ *Servicio:* {appt.service_name}\n"
        f"📅 *Fecha:* {appt.date}\n"
        f"🕐 *Hora:* {appt.time}\n"
        f"👤 *Te atendía:* {appt.staff_name}\n"
        f"💰 *Valor:* {total_formatted}\n\n"
        f"En *{shop_name}* lamentamos los inconvenientes. "
        f"Por favor contáctanos para reagendar tu cita."
    )
    
    success, error = send_whatsapp_message(appt.client_phone, msg)
    
    if success:
        print(f"[WhatsApp] ✅ Notificación de cancelación enviada al cliente {appt.client_name}")
    else:
        print(f"[WhatsApp] ❌ Falló el envío de notificación al cliente {appt.client_name}: {error}")
    
    print(f"[WhatsApp] ========================================")
    return success

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
        success, error = send_whatsapp_message(to, msg)
        if success:
            print(f"[WhatsApp] ✅ Notificación enviada exitosamente")
        else:
            print(f"[WhatsApp] ❌ Falló el envío de notificación: {error}")
        print(f"[WhatsApp] ========================================")
        return success
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
    
    success, error = send_whatsapp_message(appt.client_phone, msg)
    
    if success:
        print(f"[WhatsApp] ✅ Recordatorio enviado a {appt.client_name}")
    else:
        print(f"[WhatsApp] ❌ Falló el envío de recordatorio a {appt.client_name}: {error}")
    
    return success
