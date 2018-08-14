from __future__ import print_function
import os, sys
from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object('config')
CORS(app)
db = SQLAlchemy(app)
so = SocketIO(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import routes, models, sockets
from sensor import StateChecker
import threading
# from drivers import wire_recive
from run import arduino

@app.before_first_request
def before_first_request():
    arduino.startQueue()
    status = StateChecker()
    status.start()
