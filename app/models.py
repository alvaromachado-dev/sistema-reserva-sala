from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    cargo = db.Column(db.String(100), nullable=True)
    setor = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    reservas = db.relationship('Reserva', backref='user', lazy=True)


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    sala = db.Column(db.String(100), nullable=False, default='Sala de reunião - Miguel')
    descricao = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)