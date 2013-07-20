# -*- coding: utf-8 -*-

import psycopg2
import strings

from Crypto.Hash import SHA256
from Crypto import Random
from base64 import b64encode
from pygeoip import GeoIP
from datetime import datetime, timedelta

from flask import Flask, request, session
from flask import render_template, url_for, redirect

app = Flask(__name__)
app.secret_key = 'Zkuzxv2TXB8Q7IQ9/N4clfUYWz0Ao8H/zndS9FRxrix0'

con = psycopg2.connect(dbname='guvenlik', user='guvenlik')
cursor = con.cursor()
gip = GeoIP('/usr/share/GeoIP/GeoIP.dat')


@app.route('/')
def main():
    if 'user' in session:  # If already logged in
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))


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
                    session['is_active'] = user[4] == 1
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
    if 'user' in session:  # If already logged in
        return redirect(url_for('profile'))

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
            session['is_active'] = user[4] == 1
            session['activate_hash'] = random_str
            send_mail(user[1], 'Aktivasyon',
                      strings.activate(user[1],
                                       get_link('activate',
                                                {'h': random_str,
                                                 'mail': user[1]})))
            return redirect(url_for('profile'))
        else:
            return render_template('register.html', error='Invalid mail address')

    return render_template('register.html')


@app.route('/forgotpassword')
def forgotpassword():
    if 'user' in session:  # If already logged in
        return redirect(url_for('profile'))

    SQL_USER = 'SELECT * FROM users u WHERE u.mail = %s;'
    SQL_ACT = 'SELECT * FROM activate a WHERE a.uid = %s AND hash = %s;'
    SQL_DEL = 'DELETE FROM activate a WHERE a.id = %s;'

    code = request.args.get('h', '')
    mail = request.args.get('mail', '')

    if code and mail:
        cursor.execute(SQL_USER, (mail, ))
        user = cursor.fetchone()
        cursor.execute(SQL_ACT, (user[0], code))
        act = cursor.fetchone()
        if not act:
            return 'Hatalı İstek'

        now = datetime.now()

        cursor.execute(SQL_DEL, (act[0], ))
        con.commit()

        if (now - act[3]) > timedelta(hours=1):
            return render_template('mail.html', error='Time Limit Exceeded For Your Request')
        else:
            session['reset'] = user[0]
            return render_template('newpasswd.html')
    else:
        return render_template('mail.html')


@app.route('/requestpassword', methods=['POST'])
def reqpassword():
    if 'user' in session:  # If already logged in
        return redirect(url_for('profile'))

    SQL = 'INSERT INTO activate (uid, hash) VALUES (%s, %s);'

    if request.method == 'POST':
        mail = request.form['mail']
        user = get_user(mail)
        if user:
            random_str = generate_random_str()
            cursor.execute(SQL, (user[0], random_str))
            send_mail(user[1], 'Şifre Sıfırlama',
                      strings.reset(user[1],
                                    get_link('forgotpassword',
                                             {'h': random_str,
                                              'mail': user[1]})))
            return 'Mail adresinizi kontrol ediniz.'
        else:
            return render_template('mail.html', error='This email is not registered')
    else:
        return redirect(url_for('forgotpassword'))


@app.route('/newpassword', methods=['POST'])
def newpassword():
    if 'reset' not in session:  # There is no request
        return redirect(url_for('main'))

    SQL = 'UPDATE users SET password = %s, salt = %s WHERE id = %s;'

    passwd = request.form['yeniSifre']
    salt, hash = generate_digest(passwd)
    cursor.execute(SQL, (hash, salt, session['reset']))
    con.commit()
    session.pop('reset', None)
    return redirect(url_for('login'))


@app.route('/changepass', methods=['GET', 'POST'])
def changepassword():
    if 'user' not in session:  # If not logged in
        return redirect(url_for('login'))

    SQL = 'UPDATE users SET password = %s, salt = %s WHERE id = %s;'

    if request.method == 'POST':
        old = request.form['eskiSifre']
        new = request.form['yeniSifre']
        user = session['user']

        if verify_passwd(old, user[3], user[2]):
            salt, hash = generate_digest(new)
            cursor.execute(SQL, (hash, salt, user[0]))
            con.commit()

            # Inform User About Change
            send_mail(user[1], 'Şifre Değiştirildi',
                      strings.change(user[1], request.remote_addr))

            return redirect(url_for('profile'))
        else:
            return render_template('reset.html', error='Invalid Password')

    return render_template('reset.html')


@app.route('/remove')
def remove():
    if 'user' not in session:  # If not logged in
        return redirect(url_for('login'))

    SQL_ACT = 'SELECT * FROM activate a WHERE a.uid = %s AND hash = %s;'
    SQL_DEL_ACT = 'DELETE FROM activate a WHERE a.id = %s;'
    SQL_DEL_USR = 'DELETE FROM users u WHERE u.id = %s;'
    SQL_MAIL = 'INSERT INTO activate (uid, hash) VALUES (%s, %s);'

    code = request.args.get('h', '')
    mail = request.args.get('mail', '')
    user = session['user']

    if code and mail:
        cursor.execute(SQL_ACT, (user[0], code))
        act = cursor.fetchone()
        if not act:
            return 'Hatalı İstek'
        now = datetime.now()

        if (now - act[3]) > timedelta(hours=1):
            cursor.execute(SQL_DEL_ACT, (act[0], ))
            con.commit()
            error = 'İstek Zaman Aşımına Uğramış!'
            return render_template('profile.html', mail=user[1], error=error)
        else:
            cursor.execute(SQL_DEL_ACT, (act[0], ))
            cursor.execute(SQL_DEL_USR, (user[0], ))
            con.commit()
            return redirect(url_for('logout'))
    else:
        random_str = generate_random_str()
        cursor.execute(SQL_MAIL, (user[0], random_str))
        con.commit()

        send_mail(user[1], 'Hesal Silme',
                  strings.remove(user[1],
                                 get_link('remove', {'h': random_str,
                                                     'mail': user[1]})))

        return 'Silme işlemini tamamlamak için mailinize gönderilen linke tıklayın.'


@app.route('/activate', methods=['GET', 'POST'])
def activate():
    SQL_USER = 'SELECT * FROM users u WHERE u.mail = %s;'
    SQL_ACT = 'SELECT * FROM activate a WHERE a.uid = %s AND hash = %s;'
    SQL_DEL = 'DELETE FROM activate a WHERE a.id = %s; DELETE FROM users u WHERE u.id = %s;'
    SQL_OK = 'DELETE FROM activate a WHERE a.id = %s; UPDATE users SET is_active = 1 WHERE id = %s;'

    if request.method == 'POST':
        mail = request.form['mail']
        passwd = request.form['password']
        accode = request.form['activation']

        cursor.execute(SQL_USER, (mail, ))
        user = cursor.fetchone()
        cursor.execute(SQL_ACT, (user[0], accode))
        act = cursor.fetchone()
        if not act:
            return 'Hatalı İstek'

        now = datetime.now()

        if (now - act[3]) > timedelta(hours=1):
            cursor.execute(SQL_DEL, (act[0], user[0]))
            con.commit()
            return render_template('login.html', error='Time Limit Exceeded, Try Again')

        if verify_passwd(passwd, user[3], user[2]):
            cursor.execute(SQL_OK, (act[0], user[0]))
            con.commit()
            session['is_active'] = True
            return redirect(url_for('profile'))
        else:
            cursor.execute(SQL_DEL, (act[0], user[0]))
            con.commit()
            return render_template('login.html', error='Invalid username/password, Register Again')

    else:
        mail = request.args.get('mail', '')
        accode = request.args.get('h', '')
        return render_template('activation.html', mail=mail, accode=accode)


@app.route('/profile')
def profile():
    if 'user' not in session:  # If not logged in
        return redirect(url_for('login'))

    user = session['user']
    error = None
    active = True
    if not session['is_active']:
        error = u'Hesabınızı Aktif Etmeniz Gerekmektedir!'
        active = False
    return render_template('profile.html', mail=user[1],
                           error=error, active=active)


def get_link(action, args):
    from urllib import urlencode
    return 'https://bil553.com/{0}?{1}'.format(action,
                                               urlencode(args))


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
                             get_link('unlock', {'h': random_str})))


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
