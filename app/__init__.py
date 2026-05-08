from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import time
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import inspect, text

db = SQLAlchemy()
login_manager = LoginManager()


def garantir_coluna_sala(app):
    insp = inspect(db.engine)
    if 'reserva' in insp.get_table_names():
        colunas = [col['name'] for col in insp.get_columns('reserva')]
        if 'sala' not in colunas:
            with db.engine.begin() as conn:
                conn.execute(text("ALTER TABLE reserva ADD COLUMN sala VARCHAR(100) NOT NULL DEFAULT 'Sala de reunião - Miguel'"))
            print("✅ Coluna 'sala' adicionada na tabela reserva")


def esperar_banco(app, db, tentativas=20, delay=3):
    """
    Aguarda o banco ficar pronto antes de inicializar o app.
    Essencial em Docker.
    """
    for tentativa in range(tentativas):
        try:
            with app.app_context():
                db.create_all()
                garantir_coluna_sala(app)
            print("✅ Banco conectado e tabelas criadas!")
            return
        except (OperationalError, SQLAlchemyError) as exc:
            print(f"⏳ Aguardando banco... tentativa {tentativa + 1}/{tentativas} — {type(exc).__name__}: {exc}")
            time.sleep(delay)

    raise Exception("❌ Banco de dados indisponível")


def create_app():
    app = Flask(__name__)

    # 🔐 chave fixa (NUNCA pode mudar entre reinícios)
    app.secret_key = os.getenv(
        "SECRET_KEY",
        "sala-reuniao-chave-super-segura-123"
    )

    # 🍪 CONFIGURAÇÃO DE SESSÃO (corrige logout fantasma)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax"
    )

    # 🗄️ banco PostgreSQL/Supabase
    database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        if 'supabase.co' in database_url and 'sslmode=' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql+psycopg2://"
            f"{os.getenv('DB_USER', 'postgres')}:"
            f"{os.getenv('DB_PASSWORD', 'postgres')}@"
            f"{os.getenv('DB_HOST', 'localhost')}/"
            f"{os.getenv('DB_NAME', 'sala_reuniao')}"
        )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 🔐 Flask-Login config
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # 🔌 init DB
    db.init_app(app)

    # 📦 Blueprints
    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    # 🧠 garante banco pronto antes do app rodar
    with app.app_context():
        esperar_banco(app, db)

        # Criar usuário admin se não existir
        from .models import User
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username='Alvaro Machado').first()
        if not admin:
            admin = User(
                username='Alvaro Machado',
                password=generate_password_hash('admin123'),  # senha padrão, pode mudar
                cargo='Administrador',
                setor='TI',
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    return app