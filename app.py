import os
from flask import Flask, render_template, redirect, url_for, flash, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, logout_user, login_user, UserMixin, login_required
import forms
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_mail import Message, Mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = '4654f5dfadsrfasdr54e6rae'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'biudzetas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "MAIL_USERNAME"
app.config['MAIL_PASSWORD'] = "MAIL_PASSWORD"

mail = Mail(app)


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



bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'prisijungti'
login_manager.login_message_category = 'info'



class Vartotojas(db.Model, UserMixin):
    __tablename__ = "vartotojas"
    id = db.Column(db.Integer, primary_key=True)
    vardas = db.Column("Vardas", db.String(20), unique=True, nullable=False)
    el_pastas = db.Column("El. pašto adresas", db.String(120), unique=True, nullable=False)
    nuotrauka = db.Column(db.String(20), nullable=False, default='default.jpg')
    slaptazodis = db.Column("Slaptažodis", db.String(60), unique=True, nullable=False)
    irasai = db.relationship("Biudzetas")

    def __init__(self, vardas, el_pastas, slaptazodis):
        self.vardas = vardas
        self.el_pastas = el_pastas
        self.slaptazodis = slaptazodis

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return Vartotojas.query.get(user_id)


class Biudzetas(db.Model):
    __tablename__ = "irasas"
    id = db.Column(db.Integer, primary_key=True)
    tipas = db.Column(db.String, nullable=False)
    suma = db.Column(db.Float, nullable=False)
    info = db.Column(db.String, nullable=False)
    vartotojo_id = db.Column(db.Integer, db.ForeignKey("vartotojas.id"))
    vartotojas = db.relationship("Vartotojas")

    def __init__(self, tipas, suma, info, id):
        self.tipas = tipas
        self.suma = suma
        self.info = info
        self.vartotojo_id = id

@login_manager.user_loader
def load_user(vartotojo_id):
    return Vartotojas.query.get(int(vartotojo_id))


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


import secrets
from PIL import Image

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
    nuotrauka = url_for('static', filename='profilio_nuotraukos/' + current_user.nuotrauka)



    return render_template('paskyra.html', title='Account', form=form, nuotrauka=nuotrauka)
#
# nuotrauka = current_user.
# render_template('base.html', foto=profilio_nuotrauka)


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
        return redirect(url_for('home'))
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


class ManoModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.el_pastas == "eg@one.lt"


@app.errorhandler(404)
def klaida_404(klaida):
    return render_template("404.html"), 404

@app.errorhandler(403)
def klaida_403(klaida):
    return render_template("403.html"), 403

@app.errorhandler(500)
def klaida_500(klaida):
    return render_template("500.html"), 500

admin = Admin(app)
admin.add_view(ModelView(Biudzetas, db.session))
admin.add_view(ManoModelView(Vartotojas, db.session))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
    db.create_all()