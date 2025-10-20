# -*- coding: utf-8 -*-

'''
Filename: main.py
Author: Wout Deelen
Date: 20-10-2025
Version: 1.0
Description: This script will be used to service the website.
'''

from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/data')
def data():
    return render_template('data.html')

@app.route('/configure')
def configure():
    return render_template('configure.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot-password.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')