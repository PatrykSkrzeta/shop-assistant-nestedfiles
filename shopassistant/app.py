from flask import Flask
from flask_login import LoginManager
from mongoengine import connect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'FYDYIHGDFSIPFIDFIG'


connect('shopasistant', host='localhost', port=27017)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User
from routes import *

if __name__ == '__main__':
    app.run(debug=True)