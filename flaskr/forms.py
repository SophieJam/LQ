from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField,StringField, PasswordField
from wtforms.validators import DataRequired,Length

class RegisterForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('登録')

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('パスワード', validators=[DataRequired(), Length(min=8)])
    app_key = StringField('アプリケーションキー', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class ConsultForm(FlaskForm):
    user_input = TextAreaField('考えを共有してみよう', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CustomizeQuoteForm(FlaskForm): 
    customized_quote = TextAreaField('名言をカスタマイズしてみよう', validators=[DataRequired()]) 
    submit = SubmitField('Submit')

class PromoteToAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Promote')