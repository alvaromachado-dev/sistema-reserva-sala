from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash

from .models import db, Reserva, User
from .config import SALAS_DISPONIVEIS

main = Blueprint('main', __name__)


def parse_time(time_str):
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Formato de hora inválido: {time_str}")


def can_manage_reservation(reserva):
    return reserva and (current_user.is_admin or reserva.user_id == current_user.id)


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
        inicio = parse_time(request.form['inicio'])
        fim = parse_time(request.form['fim'])
        sala = request.form['sala']
        descricao = request.form.get('descricao')

        # 🧠 busca reservas do mesmo dia e mesma sala
        reservas_dia = Reserva.query.filter_by(data=data, sala=sala).all()

        # ⛔ validação de conflito de horário
        for r in reservas_dia:
            if (inicio < r.hora_fim) and (fim > r.hora_inicio):
                flash(f"❌ Já existe uma reserva nessa sala nesse horário.")
                return redirect('/')

        # ✔️ cria reserva
        nova = Reserva(
            data=data,
            hora_inicio=inicio,
            hora_fim=fim,
            sala=sala,
            descricao=descricao,
            user_id=current_user.id
        )

        db.session.add(nova)
        db.session.commit()

        flash("✅ Reserva criada com sucesso!")
        return redirect('/')

    # � busca e exibição de reservas
    search_description = request.args.get('search_description', '').strip()
    search_user = request.args.get('search_user', '').strip()
    search_date = request.args.get('search_date', '').strip()

    reservas_query = Reserva.query.join(User)

    if search_description:
        reservas_query = reservas_query.filter(
            Reserva.descricao.ilike(f"%{search_description}%")
        )

    if search_user:
        reservas_query = reservas_query.filter(
            User.username.ilike(f"%{search_user}%")
        )

    if search_date:
        try:
            data_busca = datetime.strptime(search_date, '%Y-%m-%d').date()
            reservas_query = reservas_query.filter(Reserva.data == data_busca)
        except ValueError:
            flash("Formato de data inválido para busca. Use AAAA-MM-DD.")

    reservas = reservas_query.order_by(
        Reserva.data, Reserva.hora_inicio
    ).all()

    return render_template(
        'index.html',
        reservas=reservas,
        search_description=search_description,
        search_user=search_user,
        search_date=search_date,
        salas_disponiveis=SALAS_DISPONIVEIS
    )


@main.route('/reservations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reservation(id):
    reserva = Reserva.query.get(id)
    if not can_manage_reservation(reserva):
        flash("❌ Acesso negado. Você não pode editar esta reserva.")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        inicio = parse_time(request.form['inicio'])
        fim = parse_time(request.form['fim'])
        sala = request.form['sala']
        descricao = request.form.get('descricao')

        if inicio >= fim:
            flash("❌ Horário de início deve ser anterior ao horário de fim.")
            return render_template('edit_reservation.html', reserva=reserva)

        reservas_dia = Reserva.query.filter(
            Reserva.data == data,
            Reserva.sala == sala,
            Reserva.id != reserva.id
        ).all()

        for r in reservas_dia:
            if (inicio < r.hora_fim) and (fim > r.hora_inicio):
                flash(f"❌ Já existe uma reserva nessa sala nesse horário.")
                return render_template('edit_reservation.html', reserva=reserva)

        reserva.data = data
        reserva.hora_inicio = inicio
        reserva.hora_fim = fim
        reserva.sala = sala
        reserva.descricao = descricao
        db.session.commit()

        flash("✅ Reserva atualizada com sucesso!")
        return redirect(url_for('main.index'))

    return render_template('edit_reservation.html', reserva=reserva, salas_disponiveis=SALAS_DISPONIVEIS)


@main.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    reserva = Reserva.query.get(id)

    if not can_manage_reservation(reserva):
        flash("❌ Acesso negado. Você não pode excluir esta reserva.")
        return redirect(url_for('main.index'))

    db.session.delete(reserva)
    db.session.commit()
    flash("🗑️ Reserva removida com sucesso.")
    return redirect(url_for('main.index'))


@main.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if not current_user.is_admin:
        flash("❌ Acesso negado. Apenas administradores podem gerenciar usuários.")
        return redirect('/')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cargo = request.form['cargo']
        setor = request.form['setor']
        is_admin = 'is_admin' in request.form

        # Verificar se usuário já existe
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("❌ Usuário já existe.")
            return redirect('/users')

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            cargo=cargo,
            setor=setor,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Usuário criado com sucesso!")
        return redirect('/users')

    users_list = User.query.all()
    return render_template('users.html', users=users_list)


@main.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        flash("❌ Acesso negado. Apenas administradores podem excluir usuários.")
        return redirect('/users')

    if current_user.id == id:
        flash("❌ Você não pode excluir sua própria conta.")
        return redirect('/users')

    user = User.query.get(id)
    if not user:
        flash("❌ Usuário não encontrado.")
        return redirect('/users')

    db.session.delete(user)
    db.session.commit()
    flash("🗑️ Usuário excluído com sucesso.")
    return redirect('/users')