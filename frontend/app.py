from flask import Flask, request, render_template, Response, redirect, url_for, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
import random
from flask import jsonify
from sqlalchemy.orm import load_only
import datetime
import json
from serializer import *
import flask_login
import os
from flask_login import current_user, login_user, logout_user
import requests
import re
from PIL import Image
from io import StringIO
import base64
import io
import cv2
import numpy as np
from recognition import *

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	DEBUG = True
	SECRET_KEY = 'W9xJeJKrUqiG9cONoM4O9ZtpZ1k4wrRJXexHtP8V'

	SENSORS_URL = 'http://10.14.194.162:5000/get_data'

	FACE_URL = 'http://10.14.194.162:5000/recognize'


app = Flask(__name__, static_url_path='/static')
app.config.from_object(Config)
login = flask_login.LoginManager(app)
login_required = flask_login.login_required
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from models import *

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

@app.route('/<path:path>')
def static_file(path):
	return app.send_static_file(path)


from flask_wtf import FlaskForm


@app.route('/login', methods=['GET', 'POST'])
def login():

	if current_user.is_authenticated:
		return redirect(url_for('home'))

	user = User.query.filter_by(name=request.form['username']).first()
	if user is None or not user.check_password(request.form['password']):

		flash('Invalid username or password')
		return redirect(url_for('login'))
	login_user(user, remember=True)
	return redirect(url_for('home'))

	return render_template('login.html', form=form)


@app.route('/', methods=['GET'])
def login_page():

	if 'username' in session:
		return redirect(url_for('home'))

	return render_template('login.html')


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login_page'))


@app.route('/user/<user_id>')
@login_required
def user(user_id):
	user = User.query.filter_by(id=user_id).first_or_404()

	return render_template('user.html', data=user)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def home():
	inhibitants = User.query.filter(User.rights.in_((2, 3)))
	friends = User.query.filter(User.rights.in_((0, 1)))
	data = {'users': inhibitants, 'friends': friends, 'sensors': get_data(Config.SENSORS_URL)}
	return render_template('index.html', data=data)


@app.route('/get_info', methods=['POST'])
@login_required
def get_info():
	return jsonify(get_data(Config.SENSORS_URL))



@app.route('/get_photo', methods=['POST'])
def get_photo():
	image_b64 = request.values['imgBase64']

	image_b64 = image_b64.replace('data:image/png;base64', '')

	data = {'image': image_b64}
	imgdata = base64.b64decode(str(image_b64))
	image = Image.open(io.BytesIO(imgdata))
	im = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2RGB)
	
	answer = get_data(Config.FACE_URL)
	print(recognize(im))


def get_data(url):
	r = requests.post(, data={})
	if r.status_code != 200:
		return {}
	return r.json()

@app.before_first_request
def create_users():

	user = User.query.get(1)

	if user is not None:
		return

	users = [
		['maciek', 2],
		['patryk', 3],
		['wojtek', 2],
		['dawid', 3],
		['roman', 0],
		['stefan', 1],
		['ania', 0],
		['iza', 1]
	]

	for data in users:
		name, rights = data
		u = User(name=name, rights=rights)
		u.set_password('1234')
		db.session.add(u)

	db.session.commit()


if __name__ == '__main__':
	db.create_all()
	
	db.init_app(app)

	app.run(host='0.0.0.0', port=8000)