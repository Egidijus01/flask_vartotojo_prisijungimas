from flask_login import UserMixin

from flask_vartotojas import db, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


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