import os

file_path = r'c:\Users\ASUS\OneDrive\Desktop\PAGINAS WEB\barberia\docker-compose.yml'

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'barber_user')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '<password>')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'evolution_db')
SECRET_KEY = os.environ.get('SECRET_KEY', '<change_me_secret_key>')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', '<change_me_evolution_key>')
AUTHENTICATION_API_KEY = os.environ.get('AUTHENTICATION_API_KEY', '<change_me_auth_key>')
DATABASE_URL = os.environ.get('DATABASE_URL', f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}')
DATABASE_CONNECTION_URI = os.environ.get('DATABASE_CONNECTION_URI', f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}?sslmode=disable')
REDIS_URI = os.environ.get('REDIS_URI', 'redis://redis:6379/0')
CACHE_REDIS_URI = os.environ.get('CACHE_REDIS_URI', 'redis://redis:6379/1')
SERVER_URL = os.environ.get('SERVER_URL', 'https://example.com')

content = f"""services:
  web:
    build: .
    restart: always
    environment:
      - TZ=America/Bogota
      - DATABASE_URL={DATABASE_URL}
      - FLASK_ENV=production
      - SECRET_KEY={SECRET_KEY}
      - EVOLUTION_API_URL=http://evolution_api:8080
      - EVOLUTION_API_KEY={EVOLUTION_API_KEY}
    volumes:
      - barberking_db:/app/instance
      - barberking_uploads:/app/app/static/uploads
    command: gunicorn --bind 0.0.0.0:80 --workers 2 --threads 2 --timeout 60 run:app
    ports:
      - "80:80"
    depends_on:
      evolution_api:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - barber_net

  evolution_api:
    image: evoapicloud/evolution-api:v2.3.7
    restart: always
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    environment:
      - TZ=America/Bogota
      - AUTHENTICATION_TYPE=apikey
      - AUTHENTICATION_API_KEY={AUTHENTICATION_API_KEY}
      - AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true
      - DATABASE_ENABLED=true
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI={DATABASE_CONNECTION_URI}
      - DATABASE_SAVE_DATA_INSTANCE=true
      - SERVER_URL={SERVER_URL}
      - REDIS_ENABLED=true
      - REDIS_URI={REDIS_URI}
      - REDIS_PREFIX_KEY=evolution
      - CACHE_REDIS_ENABLED=true
      - CACHE_REDIS_URI={CACHE_REDIS_URI}
      - CACHE_REDIS_PREFIX_KEY=cache
      - CACHE_REDIS_TTL=604800
      - CACHE_LOCAL_ENABLED=false
    ports:
      - "8085:8080"
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy
    networks:
      - barber_net

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - barberking_redis_data:/data
    networks:
      - barber_net

  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_USER={POSTGRES_USER}
      - POSTGRES_PASSWORD={POSTGRES_PASSWORD}
      - POSTGRES_DB={POSTGRES_DB}
    volumes:
      - barberking_wa_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {POSTGRES_USER} -d {POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - barber_net

networks:
  barber_net:
    driver: bridge

volumes:
  barberking_db:
  barberking_uploads:
  barberking_wa_db:
  barberking_redis_data:
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("docker-compose.yml rewritten successfully with PostgreSQL and correct formatting")
