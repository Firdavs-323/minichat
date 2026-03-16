from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('Ism', validators=[Length(max=50)])
    last_name = StringField('Familiya', validators=[Length(max=50)])
    password = PasswordField('Parol', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Parolni tasdiqlang', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Ro\'yxatdan o\'tish')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Bu username allaqachon mavjud.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu email allaqachon ro\'yxatdan o\'tgan.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Parol', validators=[DataRequired()])
    submit = SubmitField('Kirish')

class SearchForm(FlaskForm):
    search = StringField('Foydalanuvchi qidirish', validators=[DataRequired()])
    submit = SubmitField('Qidirish')

class MessageForm(FlaskForm):
    content = TextAreaField('Xabar', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Yuborish')