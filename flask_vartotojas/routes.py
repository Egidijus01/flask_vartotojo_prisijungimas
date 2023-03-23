import os
import secrets

from PIL.Image import Image
from flask import redirect, url_for, flash, render_template, request, g
from flask_login import current_user, login_user, login_required, logout_user
from flask_mail import Message


from flask_vartotojas import db, app, forms, bcrypt, mail
from flask_vartotojas.models import Vartotojas, Biudzetas


@app.route("/registruotis", methods=['GET', 'POST'])
def registruotis():
    db.create_all()
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.RegistracijosForma()
    if form.validate_on_submit():
        koduotas_slaptazodis = bcrypt.generate_password_hash(form.slaptazodis.data).decode('utf-8')
        vartotojas = Vartotojas(form.vardas.data, form.el_pastas.data, koduotas_slaptazodis)
        db.session.add(vartotojas)
        db.session.commit()
        flash('Sėkmingai prisiregistravote! Galite prisijungti', 'success')
        return redirect(url_for('index'))
    return render_template('registruotis.html', title='Register', form=form)

@app.route("/prisijungti", methods=['GET', 'POST'])
def prisijungti():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.PrisijungimoForma()
    if form.validate_on_submit():
        user = Vartotojas.query.filter_by(el_pastas=form.el_pastas.data).first()
        if user and bcrypt.check_password_hash(user.slaptazodis, form.slaptazodis.data):
            login_user(user, remember=form.prisiminti.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Prisijungti nepavyko. Patikrinkite el. paštą ir slaptažodį', 'danger')
    return render_template('prisijungti.html', title='Prisijungti', form=form)


@app.route("/atsijungti")
def atsijungti():
    logout_user()
    return redirect(url_for('index'))

@app.route("/paskyra", methods=['GET', 'POST'])
@login_required
def paskyra():
    form = forms.PaskyrosAtnaujinimoForma()
    if form.validate_on_submit():
        if form.nuotrauka.data:

            nuotrauka = save_picture(form.nuotrauka.data)
            current_user.nuotrauka = nuotrauka
        current_user.vardas = form.vardas.data
        current_user.el_pastas = form.el_pastas.data
        db.session.commit()
        flash('Tavo paskyra atnaujinta!', 'success')
        return redirect(url_for('paskyra'))
    elif request.method == 'GET':
        form.vardas.data = current_user.vardas
        form.el_pastas.data = current_user.el_pastas
    g.nuotrauka = url_for('static', filename='profilio_nuotraukos/' + current_user.nuotrauka)



    return render_template('paskyra.html', title='Account', form=form, nuotrauka=g.nuotrauka)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profilio_nuotraukos', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/irasai")
@login_required
def records():
    db.create_all()
    page = request.args.get('page', 1, type=int)
    visi_irasai = Biudzetas.query.filter_by(vartotojo_id=current_user.id).paginate(page=page, per_page=5)
    return render_template("irasai.html", visi_irasai=visi_irasai)

@app.route("/prideti_irasa", methods=['GET', 'POST'])
@login_required
def prideti():
    form = forms.PridetiIrasa()
    if form.validate_on_submit():
        # user = Vartotojas.query.filter_by(el_pastas=form.el_pastas.data).first()
        vart = current_user.get_id()
        irasas = Biudzetas(form.tipas.data, form.suma.data, form.info.data, vart)

        db.session.add(irasas)
        db.session.commit()
        flash('Sėkmingai pridejote irasa! Galite ji matyti sarase', 'success')
        return redirect(url_for('records'))
    return render_template('prideti_irasa.html', title='Įrašai', form=form)


@app.route('/taisyti/<int:id>', methods=['GET', 'POST'])
def taisyti(id):
    irasas = Biudzetas.query.get(id)
    form = forms.PridetiIrasa()
    if form.validate_on_submit():
        irasas.tipas = form.tipas.data
        irasas.suma = form.suma.data
        irasas.info = form.info.data
        db.session.commit()
        flash('Sėkmingai atnaujinote irasa! Galite ji matyti sarase', 'success')
        return redirect(url_for('records'))
    elif request.method == 'GET':
        form.tipas.data = irasas.tipas
        form.suma.data = irasas.suma
        form.info.data = irasas.info
        return render_template('prideti_irasa.html', title='Įrašai', form=form)


@app.route('/istrinti<int:id>')
def istrinti(id):
    irasas = Biudzetas.query.get(id)
    db.session.delete(irasas)
    db.session.commit()
    return redirect(url_for('records'))
@app.route("/")
def index():
    db.create_all()
    return render_template("index.html")


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Slaptažodžio atnaujinimo užklausa',
                  sender='el@pastas.lt',
                  recipients=[user.el_pastas])
    msg.body = f'''Norėdami atnaujinti slaptažodį, paspauskite nuorodą:
    {url_for('reset_token', token=token, _external=True)}
    Jei jūs nedarėte šios užklausos, nieko nedarykite ir slaptažodis nebus pakeistas.
    '''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.UzklausosAtnaujinimoForma()
    if form.validate_on_submit():
        user = Vartotojas.query.filter_by(el_pastas=form.el_pastas.data).first()
        send_reset_email(user)
        flash('Jums išsiųstas el. laiškas su slaptažodžio atnaujinimo instrukcijomis.', 'info')
        return redirect(url_for('prisijungti'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Vartotojas.verify_reset_token(token)
    if user is None:
        flash('Užklausa netinkama arba pasibaigusio galiojimo', 'warning')
        return redirect(url_for('reset_request'))
    form = forms.SlaptazodzioAtnaujinimoForma()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.slaptazodis.data).decode('utf-8')
        user.slaptazodis = hashed_password
        db.session.commit()
        flash('Tavo slaptažodis buvo atnaujintas! Gali prisijungti', 'success')
        return redirect(url_for('prisijungti'))
    return render_template('reset_token.html', title='Reset Password', form=form)




@app.errorhandler(404)
def klaida_404(klaida):
    return render_template("404.html"), 404

@app.errorhandler(403)
def klaida_403(klaida):
    return render_template("403.html"), 403

@app.errorhandler(500)
def klaida_500(klaida):
    return render_template("500.html"), 500


