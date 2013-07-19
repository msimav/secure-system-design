# -*- coding: utf-8 -*-

import psycopg2
import strings

from Crypto.Hash import SHA256
from Crypto import Random
from base64 import b64encode
from pygeoip import GeoIP

from flask import Flask, request, session
from flask import render_template, url_for, redirect

app = Flask(__name__)
app.secret_key = 'Zkuzxv2TXB8Q7IQ9/N4clfUYWz0Ao8H/zndS9FRxrix0'

con = psycopg2.connect(dbname='guvenlik', user='guvenlik')
cursor = con.cursor()
gip = GeoIP('/usr/share/GeoIP/GeoIP.dat')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:  # If already logged in
        return redirect(url_for('profile'))

    if request.method == 'POST':
        mail = request.form['mail']
        passwd = request.form['password']

        if mail and passwd:
            user = get_user(mail)
            if not user:  # prevent timing attack
                user = (-1, '', generate_random_str(), generate_random_str())

            user_pass = user[2]
            if verify_passwd(passwd, user[3], user_pass):
                if user[5] == get_country(request.remote_addr):
                    session['user'] = user
                    session['is_active'] = user[4]
                    return redirect(url_for('profile'))
                else:
                    random_str = generate_random_str()
                    lock_user(user, random_str)
                    return render_template('login.html', error='Your Account Locked')

        return render_template('login.html', error='Invalid username/password')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def create_user():
    SQL = 'INSERT INTO users (mail, password, salt, is_active, last_loc) VALUES (%s, %s, %s, 0, %s) RETURNING *;'
    SQL_MAIL = 'INSERT INTO activate (uid, hash) VALUES (%s, %s);'

    if request.method == 'POST':
        mail = request.form['mail']
        passwd = request.form['password']

        if not get_user(mail):
            salt, hash = generate_digest(passwd)
            cursor.execute(SQL, (mail, hash, salt, get_country(request.remote_addr)))
            user = cursor.fetchone()

            random_str = generate_random_str()
            cursor.execute(SQL_MAIL, (user[0], random_str))
            con.commit()

            session['user'] = user
            session['is_active'] = user[4]
            session['activate_hash'] = random_str
            send_mail(user[1], 'Aktivasyon',
                      strings.activate(user[1],
                                       get_link('activate', random_str)))
            return redirect(url_for('profile'))
        else:
            return render_template('register.html', error='Invalid mail address')

    return render_template('register.html')


@app.route('/forgotpassword')
def forgotpassword():
    pass


@app.route('/activate')
def activate():
    pass


@app.route('/profile')
def profile():
    if 'user' not in session:  # If not logged in
        return redirect(url_for('login'))

    user = session['user']
    error = None
    if not session['is_active']:
        error = u'Hesabınızı Aktif Etmeniz Gerekmektedir!'
    return render_template('profile.html', mail=user[1], error=error)


def get_link(action, random_str):
    from urllib import urlencode
    return 'http://10.10.29.39/{0}?{1}'.format(action,
                                               urlencode({'h': random_str}))


def send_mail(to, subject, mail):
    from email.mime.text import MIMEText
    from subprocess import Popen, PIPE

    msg = MIMEText(mail)
    msg['From'] = 'tahirelgamal@gmail.com'
    msg['To'] = to
    msg['Subject'] = subject
    p = Popen(["msmtp", "-t"], stdin=PIPE)
    p.communicate(msg.as_string())


def lock_user(user, random_str):
    SQL = 'UPDATE users SET is_active = 0 WHERE id = %s;'
    SQL_MAIL = 'INSERT INTO activate (uid, hash) VALUES (%s, %s);'

    cursor.execute(SQL, (user[0], ))
    cursor.execute(SQL_MAIL, (user[0], random_str))
    con.commit()

    send_mail(user[1], 'Aktivasyon',
              strings.unlock(user[1],
                             get_link('activate', random_str)))


def get_country(ip):
    country = gip.country_code_by_addr(ip)
    if not country:
        country = 'RSVD'
        return country


def get_user(mail):
    SQL = 'SELECT * FROM users u WHERE u.mail = %s;'
    cursor.execute(SQL, (mail, ))
    return cursor.fetchone()


def generate_random_str():
    return b64encode(Random.new().read(48))


def generate_digest(passwd):
    salt = b64encode(Random.new().read(128))
    return (salt, digest_passwd(passwd, salt))


def digest_passwd(passwd, salt):
    hash = SHA256.new()
    hash.update(salt + passwd)
    message = hash.digest()

    for i in range(1000):
        hash = SHA256.new()
        hash.update(message)
        message = hash.digest()

    return hash.hexdigest()


def verify_passwd(passwd, salt, digest):
    computed_digest = digest_passwd(passwd, salt)
    result = 0
    for x, y in zip(computed_digest, digest):
        result |= ord(x) ^ ord(y)
        return result == 0


if __name__ == '__main__':
    app.run(debug=True)
