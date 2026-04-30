from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required, current_user
from datetime import datetime

from .models import db, Reserva

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():

    # 🔍 DEBUG: confirma se a rota está sendo acessada
    print("🔥 CHEGOU NA INDEX")

    # 🔍 DEBUG: verifica autenticação real neste request
    print("AUTH:", current_user.is_authenticated)
    print("USER:", current_user.id if current_user.is_authenticated else None)

    if request.method == 'POST':

        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        inicio = datetime.strptime(request.form['inicio'], '%H:%M').time()
        fim = datetime.strptime(request.form['fim'], '%H:%M').time()
        descricao = request.form.get('descricao')

        # 🧠 busca reservas do mesmo dia
        reservas_dia = Reserva.query.filter_by(data=data).all()

        # ⛔ validação de conflito de horário
        for r in reservas_dia:
            if (inicio < r.hora_fim) and (fim > r.hora_inicio):
                flash("❌ Já existe uma reserva nesse horário.")
                return redirect('/')

        # ✔️ cria reserva
        nova = Reserva(
            data=data,
            hora_inicio=inicio,
            hora_fim=fim,
            descricao=descricao,
            user_id=current_user.id
        )

        db.session.add(nova)
        db.session.commit()

        flash("✅ Reserva criada com sucesso!")
        return redirect('/')

    # 📋 lista reservas
    reservas = Reserva.query.order_by(
        Reserva.data, Reserva.hora_inicio
    ).all()

    return render_template('index.html', reservas=reservas)


@main.route('/delete/<int:id>')
@login_required
def delete(id):

    print("🔥 CHEGOU NO DELETE")
    print("AUTH DELETE:", current_user.is_authenticated)

    reserva = Reserva.query.get(id)

    if reserva:
        db.session.delete(reserva)
        db.session.commit()
        flash("🗑️ Reserva removida com sucesso.")

    return redirect('/')