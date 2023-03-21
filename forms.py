from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, StringField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, EqualTo
import app


class RegistracijosForma(FlaskForm):
    vardas = StringField('Vardas', [DataRequired()])
    el_pastas = StringField('El. paštas', [DataRequired()])
    slaptazodis = PasswordField('Slaptažodis', [DataRequired()])
    patvirtintas_slaptazodis = PasswordField("Pakartokite slaptažodį", [EqualTo('slaptazodis', "Slaptažodis turi sutapti.")])
    submit = SubmitField('Prisiregistruoti')

    # def validate_vardas(self, vardas):
    #     vartotojas = app.Vartotojas.query.filter_by(vardas=vardas.data).first()
    #     if vartotojas:
    #         raise ValidationError('Šis vardas panaudotas. Pasirinkite kitą.')
    #
    # def validate_el_pastas(self, el_pastas):
    #     vartotojas = app.Vartotojas.query.filter_by(el_pastas=el_pastas.data).first()
    #     if vartotojas:
    #         raise ValidationError('Šis el. pašto adresas panaudotas. Pasirinkite kitą.')


class PrisijungimoForma(FlaskForm):
    el_pastas = StringField('El. paštas', [DataRequired()])
    slaptazodis = PasswordField('Slaptažodis', [DataRequired()])
    prisiminti = BooleanField("Prisiminti mane")
    submit = SubmitField('Prisijungti')

class PridetiIrasa(FlaskForm):
    tipas = SelectField('Irašo tipas', choices=[('Pajamu'), ('Išlaidų')])
    suma = StringField('Suma', [DataRequired()])
    info = TextAreaField("Papildoma informacija", [DataRequired()])
    submit = SubmitField('Irasyti')

from flask_wtf.file import FileField, FileAllowed

class PaskyrosAtnaujinimoForma(FlaskForm):
    vardas = StringField('Vardas', [DataRequired()])
    el_pastas = StringField('El. paštas', [DataRequired()])
    nuotrauka = FileField('Atnaujinti profilio nuotrauką', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Atnaujinti')

    def validate_vardas(self, vardas):
        if vardas.data != app.current_user.vardas:
            vartotojas = app.Vartotojas.query.filter_by(vardas=vardas.data).first()
            if vartotojas:
                raise ValidationError('Šis vardas panaudotas. Pasirinkite kitą.')

    def validate_el_pastas(self, el_pastas):
        if el_pastas.data != app.current_user.el_pastas:
            vartotojas = app.Vartotojas.query.filter_by(el_pastas=el_pastas.data).first()
            if vartotojas:
                raise ValidationError('Šis el. pašto adresas panaudotas. Pasirinkite kitą.')
