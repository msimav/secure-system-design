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
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mail = request.form['mail']
        passwd = request.form['password']

        if mail:
            user = get_user(mail)
            user_pass = user[2]
            if not user:  # timing attack
                return render_template('login.html', error='Invalid username/password')

            if verify_passwd(passwd, user[3], user_pass):
                if user[5] == get_country(request.remote_addr):
                    session['logged_in'] = True
                    session['user'] = user
                    return redirect(url_for('profile'))
                else:
                    lock_user(user)
                    return render_template('login.html', error='Your Account Locked')
            else:
                return render_template('login.html', error='Invalid username/password')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def create_user():
    SQL = 'INSERT INTO users (mail, password, salt, is_active, last_loc) VALUES (%s, %s, %s, 1, %s) RETURNING *;'

    if request.method == 'POST':
        mail = request.form['mail']
        passwd = request.form['password']

        if not get_user(mail):
            salt, hash = generate_digest(passwd)
            cursor.execute(SQL, (mail, hash, salt, get_country(request.remote_addr)))
            user = cursor.fetchone()
            con.commit()

            session['logged_in'] = True
            session['user'] = user
            return redirect(url_for('profile'))
        else:
            return render_template('register.html', error='Invalid mail address')

    return render_template('register.html')


@app.route('/profile')
def profile():
    mail = 'burakdikili@gmail.com'
    send_mail(mail, 'Aktivasyon Maili',
              strings.activate(mail, 'hebele hubele'))
    return 'Dogru Calisiyor'


def send_mail(to, subject, mail):
    from email.mime.text import MIMEText
    from subprocess import Popen, PIPE

    msg = MIMEText(mail)
    msg['From'] = 'tahirelgamal@gmail.com'
    msg['To'] = to
    msg['Subject'] = subject
    p = Popen(["msmtp", "-t"], stdin=PIPE)
    p.communicate(msg.as_string())


def lock_user(user):
    pass


def get_country(ip):
    country = gip.country_code_by_addr(ip)
    if not country:
        country = 'RSVD'
        return country


def get_user(mail):
    SQL = 'SELECT * FROM users u WHERE u.mail = %s;'
    cursor.execute(SQL, (mail, ))
    return cursor.fetchone()


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
