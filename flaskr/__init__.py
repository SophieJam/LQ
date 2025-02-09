from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = app.secret_key
csrf = CSRFProtect(app)

import flaskr.main
