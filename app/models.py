from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class BaseModel(db.Model):
    __abstract__ = True
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Admin(UserMixin, BaseModel):
    __tablename__ = 'admins'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


class Service(BaseModel):
    __tablename__ = 'services'
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(100), nullable=False)
    description      = db.Column(db.String(300))
    price            = db.Column(db.Integer, nullable=False, default=0)
    emoji            = db.Column(db.String(20), default='✂')
    image_url        = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    gender           = db.Column(db.String(10), nullable=False, default='male', index=True)
    active           = db.Column(db.Boolean, default=True, index=True)

    __table_args__ = (
        db.Index('ix_service_gender_active', 'gender', 'active'),
    )


class Staff(BaseModel):
    __tablename__ = 'staff'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    title       = db.Column(db.String(100))
    experience  = db.Column(db.String(50))
    stars       = db.Column(db.Integer, default=5)
    emoji       = db.Column(db.String(20), default='💈')
    image_url   = db.Column(db.Text)
    specialties = db.Column(db.String(200))
    phone       = db.Column(db.String(20))
    instagram   = db.Column(db.String(100))
    gender      = db.Column(db.String(10), nullable=False, default='male', index=True)
    active      = db.Column(db.Boolean, default=True, index=True)

    __table_args__ = (
        db.Index('ix_staff_gender_active', 'gender', 'active'),
    )


class Appointment(BaseModel):
    __tablename__ = 'appointments'
    id               = db.Column(db.Integer, primary_key=True)
    client_name      = db.Column(db.String(100), nullable=False)
    client_phone     = db.Column(db.String(20), nullable=False)
    gender           = db.Column(db.String(10), nullable=False)
    service_name     = db.Column(db.String(100), nullable=False)
    staff_name       = db.Column(db.String(100), nullable=False, index=True)
    date             = db.Column(db.String(10), nullable=False, index=True)
    time             = db.Column(db.String(5), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    total            = db.Column(db.String(30))
    status           = db.Column(db.String(20), default='Pendiente', index=True)
    is_free_cut      = db.Column(db.Boolean, default=False, index=True)
    reminder_sent    = db.Column(db.Boolean, default=False, index=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        # Índice compuesto para búsqueda de horarios ocupados
        db.Index('ix_appt_date_time_staff', 'date', 'time', 'staff_name'),
        # Índice para búsqueda por cliente
        db.Index('ix_appt_phone_status', 'client_phone', 'status'),
    )


class ShopConfig(BaseModel):
    __tablename__ = 'shop_config'
    id        = db.Column(db.Integer, primary_key=True)
    key       = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value     = db.Column(db.Text, default='')


class Review(BaseModel):
    __tablename__ = 'reviews'
    id          = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    rating      = db.Column(db.Integer, nullable=False)
    comment     = db.Column(db.Text)
    staff_name  = db.Column(db.String(100))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class InactiveDay(BaseModel):
    __tablename__ = 'inactive_days'
    id          = db.Column(db.Integer, primary_key=True)
    staff_name  = db.Column(db.String(100), nullable=False, index=True)
    date        = db.Column(db.String(10), nullable=False, index=True)  # formato YYYY-MM-DD
    reason      = db.Column(db.String(200), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('staff_name', 'date', name='uq_staff_date'),
        db.Index('ix_staff_date', 'staff_name', 'date'),
    )


def seed_data():
    import os
    import secrets

    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USER', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if not DEFAULT_ADMIN_PASSWORD:
        DEFAULT_ADMIN_PASSWORD = secrets.token_urlsafe(16)
        print('[Seed] WARNING: ADMIN_PASSWORD not set; generated temporary admin password.')

    existing_admin = Admin.query.order_by(Admin.id).first()
    display_password = DEFAULT_ADMIN_PASSWORD

    # Si se pide reset explícito vía variable de entorno
    if os.environ.get('ADMIN_RESET', '').lower() == 'true' and existing_admin:
        existing_admin.username = DEFAULT_ADMIN_USERNAME
        existing_admin.set_password(DEFAULT_ADMIN_PASSWORD)
        db.session.commit()
        print(f"[Seed] ✅ Admin reseteado (ADMIN_RESET=true): {DEFAULT_ADMIN_USERNAME}/{display_password}")
        return

    if existing_admin:
        print(f"[Seed] Admin ya existe (username={existing_admin.username}), se respetan credenciales actuales")
        return

    admin = Admin(username=DEFAULT_ADMIN_USERNAME)
    admin.set_password(DEFAULT_ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    print(f"[Seed] ✅ Admin creado: {DEFAULT_ADMIN_USERNAME}/{display_password}")

    male_services = [
        Service(name='Corte de Cabello',  description='Corte clásico o moderno adaptado a tu estilo personal', price=25000, emoji='💇', gender='male'),
        Service(name='Corte + Barba',     description='Combo completo: cabello y barba con acabado perfecto',   price=40000, emoji='✂',  gender='male'),
        Service(name='Afeitado Clásico',  description='Afeitado con navaja, toalla caliente y aceites esenciales', price=30000, emoji='🪒', gender='male'),
        Service(name='Corte + Cejas',     description='Corte de cabello más diseño y perfilado de cejas',       price=32000, emoji='👁',  gender='male'),
        Service(name='Degradado Fade',    description='Degradado preciso desde cero hasta la longitud deseada', price=28000, emoji='⚡',  gender='male'),
        Service(name='Combo VIP Total',   description='Corte, barba, cejas y tratamiento de keratina premium',  price=65000, emoji='👑',  gender='male'),
        Service(name='Tinte & Color',     description='Coloración profesional con productos de alta calidad',   price=50000, emoji='🎨',  gender='male'),
        Service(name='Limpieza Facial',   description='Limpieza profunda, vapor y mascarilla revitalizante',    price=35000, emoji='✨',  gender='male'),
    ]

    female_services = [
        Service(name='Corte Femenino',      description='Corte personalizado según tu tipo de cabello y rostro',   price=35000,  emoji='✂',       gender='female'),
        Service(name='Peinado & Styling',   description='Peinado profesional para cualquier ocasión especial',     price=40000,  emoji='💁‍♀️', gender='female'),
        Service(name='Tinte Completo',      description='Coloración completa con productos de alta calidad',       price=80000,  emoji='🎨',       gender='female'),
        Service(name='Mechas & Highlights', description='Mechas balayage, californianas o de fantasía',            price=90000,  emoji='✨',       gender='female'),
        Service(name='Keratina',            description='Tratamiento de alisado y nutrición con keratina premium', price=120000, emoji='💎',       gender='female'),
        Service(name='Manicure',            description='Manicure clásico, semipermanente o acrílico',             price=25000,  emoji='💅',       gender='female'),
        Service(name='Pedicure',            description='Pedicure completo con exfoliación y masaje',              price=30000,  emoji='🦶',       gender='female'),
        Service(name='Cejas & Pestañas',    description='Diseño de cejas y lifting de pestañas profesional',       price=45000,  emoji='👁',       gender='female'),
    ]

    barbers = [
        Staff(name='Alejandro Ruiz',   title='Master Barber',  experience='8 años', stars=5, emoji='👨‍🦱', specialties='Fades, Diseños',   phone='3001112233', gender='male'),
        Staff(name='Carlos Medina',    title='Senior Barber',  experience='6 años', stars=5, emoji='🧔',    specialties='Barba, Clásicos',  phone='3012223344', gender='male'),
        Staff(name='Sebastián Torres', title='Expert Barber',  experience='4 años', stars=4, emoji='👨‍🦳', specialties='Color, Modernos',  phone='3023334455', gender='male'),
        Staff(name='Felipe Gómez',     title='Barber Artist',  experience='5 años', stars=5, emoji='👱',    specialties='Diseños, VIP',     phone='3034445566', gender='male'),
        Staff(name='Andrés Cano',      title='Classic Barber', experience='7 años', stars=4, emoji='👨',    specialties='Afeitado, Cejas',  phone='3045556677', gender='male'),
    ]

    stylists = [
        Staff(name='Valentina Ríos',  title='Master Stylist',   experience='7 años', stars=5, emoji='👩‍🦰', specialties='Tintes, Keratina', phone='3056667788', gender='female'),
        Staff(name='Camila Herrera',  title='Color Specialist',  experience='5 años', stars=5, emoji='👩‍🦱', specialties='Mechas, Color',    phone='3067778899', gender='female'),
        Staff(name='Laura Jiménez',   title='Senior Stylist',    experience='6 años', stars=4, emoji='👩',    specialties='Cortes, Peinados', phone='3078889900', gender='female'),
        Staff(name='Daniela Moreno',  title='Nail & Beauty',     experience='4 años', stars=5, emoji='💅',    specialties='Manicure, Uñas',   phone='3089990011', gender='female'),
    ]

    for item in male_services + female_services + barbers + stylists:
        db.session.add(item)

    db.session.commit()
