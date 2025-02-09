from flaskr import app
from flask import Flask, render_template, request, redirect, session, url_for, flash, Response
from .forms import PromoteToAdminForm, RegisterForm, LoginForm, CustomizeQuoteForm, ConsultForm
from .db import fetch_random_quote, create_user, get_user_password, get_user_history,get_user_role,update_user_role,create_tables,get_user
from .ai import generate_ai_feedback, generate_image, generate_ai_response, generate_image_prompt
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from datetime import timedelta, datetime
from functools import wraps
from markupsafe import escape
from flask_session import Session
from redis import Redis

app.secret_key = os.urandom(24)

app.login_key = os.getenv("Application_key")
admin_username = os.getenv("Admin_user")
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
LOCKOUT_TIME = 15
lockout_info = {}
failed_attempts = {}

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1) 

csrf = CSRFProtect(app)

allowed_referers = [
    "http://127.0.0.1:5000/register",
    "http://127.0.0.1:5000/login",
    "http://127.0.0.1:5000/logout",
    "http://127.0.0.1:5000/home",
    "http://127.0.0.1:5000/consult",
    "http://127.0.0.1:5000/submit",
    "http://127.0.0.1:5000/customize",
    "http://127.0.0.1:5000/dashboard",
    "http://127.0.0.1:5000/promote_to_admin",
    "http://127.0.0.1:5000/index"

]
# index以降のすべてのURLをドメイン取得後に掲載

# Redisをセッションを保持するキャッシュとして機能させる
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SESSION_REDIS'] = Redis(host='localhost', port=6379)
# Session(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('セッションが切れました。再度ログインしてください。', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                flash('ログインが必要です。', 'error')
                return redirect(url_for('login', next=request.url))
            user_role = session.get('user_role')
            if user_role != role:
                flash('アクセス権限がありません。', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.before_request
def make_session_permanent():
    session.permanent = True
    session.modified = True

def regenerate_session():
    old_data = dict(session)
    session.clear()
    session.update(old_data)

def create_response(content, status=200):
    response = Response(content, status=status)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "img-src 'self' data:; " 
        "style-src 'self' 'unsafe-inline'; " 
        "script-src 'self' 'unsafe-inline'; " 
        "reflected-xss 'block';"
    )
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

def check_referer():
    referer = request.headers.get('Referer')
    if referer:
        for allowed_referer in allowed_referers:
            if referer.startswith(allowed_referer):
                return True
    return False

def sanitize_input(input_str):
    sanitized_str = input_str.replace('\n', '').replace('\r', '')
    return sanitized_str

@app.route('/')
def index():
    return create_response(render_template('index.html'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        if not check_referer():
            return create_response("不正なリンク元からのリクエストです。", 403)
        username = sanitize_input(escape(request.form['username']))
        password = sanitize_input(escape(request.form['password']))
        if username == admin_username:
            user_role = 'admin'
        else:
            user_role = 'user'
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            return create_response("ユーザー名は英数字のみ使用できます")
        if not password or len(password) < 8:
            return create_response("パスワードは8文字以上である必要があります")
        create_user(username, password,user_role)
        return redirect(url_for('login'))
    return create_response(render_template('register.html', form=form))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    form = LoginForm()
    if request.method == 'POST':
        if not check_referer():
            return create_response("不正なリンク元からのリクエストです。", 403)
        username = sanitize_input(escape(request.form['username']))
        password = sanitize_input(escape(request.form['password']))
        app_key = sanitize_input(escape(request.form['app_key']))

        if not re.match(r'^[a-zA-Z0-9]+$', username):
            flash("無効なユーザー名", 'error')
            return redirect(url_for('login'))

        if username in lockout_info:
            lockout_time = lockout_info[username]
            if datetime.now() < lockout_time:
                flash("アカウントがロックされています。しばらくしてから再試行してください。", 'error')
                return redirect(url_for('login'))

        ip_address = request.remote_addr
        if ip_address in failed_attempts and failed_attempts[ip_address] >= 50:
            lockout_info[ip_address] = datetime.now() + timedelta(minutes=LOCKOUT_TIME)
            flash("アカウントがロックされています。", 'error')
            return redirect(url_for('login'))

        if not app_key or app_key != app.login_key:
            failed_attempts[ip_address] = failed_attempts.get(ip_address, 0) + 1
            flash("無効なアプリケーションキー", 'error')
            return redirect(url_for('login'))

        stored_password = get_user_password(username)
        if stored_password and check_password_hash(stored_password, password):
            regenerate_session()
            session['user_role'] = get_user_role(username)
            session['username'] = username
            failed_attempts[ip_address] = 0
            lockout_info.pop(ip_address, None)
            return redirect(url_for('home'))
        else:
            failed_attempts[ip_address] = failed_attempts.get(ip_address, 0) + 1
            flash("認証失敗", 'error')
    return create_response(render_template('login.html', form=form))

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/home')
@login_required
def home():
    quotes = fetch_random_quote()
    session['quotes'] = quotes
    session['chat_log'] = []
    prompt = generate_image_prompt(quotes.get('quote'), quotes.get('author_name'))
    image_url = generate_image(prompt)
    session['image_url'] = image_url
    # Redis sessionがまだ使えないためimage_url=image_urlとするがimage_url=session['image_url']と変えるべし
    return create_response(render_template('home.html', quotes=quotes, image_url=image_url))

@app.route('/consult')
@login_required
def consult():
    form = ConsultForm()
    quotes = session.get('quotes', [])
    chat_log = session.get('chat_log', [])
    image_url = session.get('image_url')
    return create_response(render_template('consult.html', quotes=quotes, chat_log=chat_log, image_url=image_url, form=form))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    if not check_referer():
        return create_response("不正なリンク元からのリクエストです。", 403)
    user_input = sanitize_input(escape(request.form.get('user_input', '')))
    quotes = session.get('quotes', {})
    quote_text = quotes.get('quote')
    author_name = quotes.get('author_name')
    if user_input:
        chat_log = session.get('chat_log', [])
        chat_log.append(f"あなた: {user_input}")
        ai_response = generate_ai_response(user_input, quote_text, author_name)
        chat_log.append(f"AI: {ai_response}")
        session['chat_log'] = chat_log
    return redirect(url_for('consult'))

@app.route('/customize', methods=['GET', 'POST'])
@login_required
def customize():
    form = CustomizeQuoteForm()
    original_quote = session.get('quotes', {}).get('quote')
    author_name = session.get('quotes', {}).get('author_name')

    if form.validate_on_submit():
        if not check_referer():
            return create_response("不正なリンク元からのリクエストです。", 403)
        customized_quote = sanitize_input(escape(form.customized_quote.data))
        ai_feedback = generate_ai_feedback(customized_quote, original_quote, author_name)
        return create_response(
            render_template('customize.html',
            quotes={"quote": original_quote},
            customized_quote=customized_quote,
            ai_feedback=ai_feedback,
            form=form
        ))

    return create_response(render_template('customize.html', quotes={"quote": original_quote}, form=form))

@app.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    if 'username' in session:
        username = session['username']
        history = get_user_history(username)
        return create_response(render_template('dashboard.html', username=username, history=history))
    return render_template('dashboard.html')

@app.route('/promote_to_admin', methods=['GET', 'POST'])
@role_required('admin')
def promote_to_admin():
    form = PromoteToAdminForm()
    if form.validate_on_submit():
        username = form.username.data
        user = get_user(username)
        if user:
            update_user_role(username, 'admin')
            flash(f'{username} が管理者に昇進されました。', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'ユーザー {username} が見つかりませんでした。', 'error')
    return render_template('promote_to_admin.html', form=form)


if __name__ == '__main__':
    app.run(debug=True) 