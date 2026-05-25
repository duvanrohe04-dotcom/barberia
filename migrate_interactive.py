#!/usr/bin/env python3
"""
Script interactivo para migrar de SQLite a PostgreSQL
Ejecutar: python migrate_interactive.py
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_step(num, text):
    print(f"\n[PASO {num}] {text}")
    print("-" * 60)

def ask_yes_no(question):
    while True:
        response = input(f"\n❓ {question} (s/n): ").lower().strip()
        if response in ['s', 'y', 'si', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("  Por favor, responde 's' o 'n'")

def run_command(cmd, description):
    print(f"\n▶️  {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Éxito")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_files():
    """Verificar que existen los archivos necesarios"""
    print_step(1, "Verificar archivos necesarios")
    
    files_needed = {
        'instance/barberking.db': 'Base de datos SQLite actual',
        'setup_postgres.py': 'Script de configuración PostgreSQL',
        'migrate_data_safely.py': 'Script de migración de datos',
        'docker-compose.yml': 'Configuración Docker',
        'app/__init__.py': 'App Flask'
    }
    
    all_exist = True
    for file, desc in files_needed.items():
        if Path(file).exists():
            print(f"  ✅ {file} - {desc}")
        else:
            if 'barberking.db' in file:
                print(f"  ⚠️  {file} - {desc} (se creará en local)")
            else:
                print(f"  ❌ {file} - {desc} (FALTA)")
                all_exist = False
    
    return all_exist

def setup_postgres():
    """Ejecutar setup de PostgreSQL"""
    print_step(2, "Configurar PostgreSQL")
    
    print("""
  Necesito que PostgreSQL esté corriendo.
  
  Opciones:
  1. Docker: docker-compose up -d postgres redis
  2. Local: Si tienes PostgreSQL instalado, asegúrate que está corriendo
  3. DBeaver: Conectar a tu instancia PostgreSQL existente
    """)
    
    if ask_yes_no("¿PostgreSQL está corriendo?"):
        print("\n  Iniciando configuración...")
        if run_command("python setup_postgres.py", "Crear base de datos barberking_db"):
            return True
        else:
            print("  ⚠️  Hubo un error. Verifica que PostgreSQL está accesible.")
            return False
    else:
        print("  ⚠️  Por favor, inicia PostgreSQL primero.")
        print("  Ejecuta: docker-compose up -d postgres redis")
        return False

def backup_sqlite():
    """Hacer backup de SQLite"""
    print_step(3, "Backup de seguridad")
    
    if not Path('instance/barberking.db').exists():
        print("  ⚠️  No se encontró base de datos SQLite")
        print("  (Esto es normal si es la primera vez que corres en PostgreSQL)")
        return True
    
    print("  Creando backup antes de migrar...")
    from datetime import datetime
    import shutil
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"backup_sqlite_{timestamp}.db"
    
    try:
        shutil.copy('instance/barberking.db', backup_path)
        print(f"  ✅ Backup creado: {backup_path}")
        return True
    except Exception as e:
        print(f"  ❌ Error creando backup: {e}")
        return False

def migrate_data():
    """Migrar datos de SQLite a PostgreSQL"""
    print_step(4, "Migrar datos")
    
    if not Path('instance/barberking.db').exists():
        print("  ⓘ No hay datos SQLite para migrar")
        print("  (Esto es normal en una instalación nueva)")
        return True
    
    print("  ⚠️  IMPORTANTE: Esto va a migrar todos tus datos.")
    print("  Se creó un BACKUP por seguridad.")
    
    if ask_yes_no("¿Deseas continuar con la migración?"):
        if run_command("python migrate_data_safely.py", "Migrar datos a PostgreSQL"):
            return True
        else:
            print("  ❌ Error en la migración")
            if ask_yes_no("¿Deseas restaurar desde backup?"):
                import shutil
                backups = sorted(Path('.').glob('backup_sqlite_*.db'), reverse=True)
                if backups:
                    backup_file = backups[0]
                    shutil.copy(backup_file, 'instance/barberking.db')
                    print(f"  ✅ Restaurado: {backup_file}")
            return False
    else:
        print("  Migración cancelada.")
        return False

def test_local():
    """Probar la app en local"""
    print_step(5, "Verificar en Local")
    
    print("""
  Ahora vas a correr la app en local para verificar que los datos migraron.
  
  ⚠️  IMPORTANTE:
    - No establecer DATABASE_URL en local
    - La app usará SQLite automáticamente
    - Los datos deben estar en 'instance/barberking.db'
    """)
    
    if ask_yes_no("¿Deseas correr la app en local ahora? (http://localhost:81)"):
        print("\n  Iniciando Flask...")
        print("  (Presiona Ctrl+C para detener)")
        try:
            subprocess.run("python run.py", shell=True)
        except KeyboardInterrupt:
            print("\n  ✅ App detenida")
        return True
    else:
        print("  Puedes correr la app después con: python run.py")
        return True

def configure_coolify():
    """Instrucciones para Coolify"""
    print_step(6, "Configurar Coolify")
    
    print("""
  📍 PASOS EN COOLIFY:
  
  1. Ve a tu proyecto en Coolify
  2. Busca 'Settings' → 'Environment'
  3. Busca la variable: DATABASE_URL
  4. Cambia su valor a:
    postgresql://barber_user:<POSTGRES_PASSWORD>@postgres:5432/barberking_db
  
  5. Guarda cambios
  6. Ve a 'Deployments' y haz REDEPLOY
  7. Espera a que termine (2-5 minutos)
  8. Verifica en tu dominio que funciona
  
  ✅ Deberías ver:
    - Login funciona
    - Todos los servicios visibles
    - Todo el staff visible
    - Citas históricas cargadas
    - Nuevas citas se guardan
    """)
    
    if ask_yes_no("¿Ya completaste los pasos en Coolify?"):
        if ask_yes_no("¿Funciona todo correctamente en Coolify?"):
            return True
        else:
            print("  ⚠️  Revisa los logs en Coolify → Deployments → Logs")
            return False
    else:
        print("  Completaremos esto después. Recordatorio:")
        print("  DATABASE_URL = postgresql://barber_user:<POSTGRES_PASSWORD>@postgres:5432/barberking_db")
        return True

def main():
    print_header("🚀 MIGRACIÓN SQLITE → POSTGRESQL")
    
    steps = [
        ("Verificar archivos", check_files),
        ("Configurar PostgreSQL", setup_postgres),
        ("Backup de seguridad", backup_sqlite),
        ("Migrar datos", migrate_data),
        ("Verificar en local", test_local),
        ("Configurar Coolify", configure_coolify),
    ]
    
    completed = 0
    failed = False
    
    for step_name, step_func in steps:
        try:
            if step_func():
                completed += 1
                print(f"\n✅ {step_name} - COMPLETADO")
            else:
                print(f"\n❌ {step_name} - FALLÓ")
                failed = True
                if not ask_yes_no("¿Continuar de todas formas?"):
                    break
        except Exception as e:
            print(f"\n❌ {step_name} - ERROR: {e}")
            failed = True
            if not ask_yes_no("¿Continuar de todas formas?"):
                break
    
    print_header("📊 RESUMEN")
    print(f"\nPasos completados: {completed}/{len(steps)}")
    
    if not failed:
        print("""
✅ ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!

Tu base de datos ha sido migrada:
  - Local (Windows): SQLite ✅
  - Coolify (Servidor): PostgreSQL ✅

Todos tus datos están preservados.
        """)
    else:
        print("""
⚠️  Hubo algunos problemas.

Revisa:
  1. Los logs de PostgreSQL
  2. Que el archivo de backup existe
  3. Los logs de la app (python run.py)
        """)
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario")
        sys.exit(1)
