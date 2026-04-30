from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import time
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()
login_manager = LoginManager()


def esperar_banco(app, db, tentativas=10, delay=3):
    """
    Aguarda o MySQL ficar pronto antes de inicializar o app.
    Essencial em Docker.
    """
    for tentativa in range(tentativas):
        try:
            with app.app_context():
                db.create_all()
            print("✅ Banco conectado e tabelas criadas!")
            return
        except OperationalError:
            print(f"⏳ Aguardando banco... tentativa {tentativa + 1}/{tentativas}")
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

    # 🗄️ banco MySQL (Docker-friendly)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}/"
        f"{os.getenv('DB_NAME')}"
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

    return app