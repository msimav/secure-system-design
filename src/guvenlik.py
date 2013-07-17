from flask import Flask
from pymongo import MongoClient
from Crypto.Hash import SHA256
from Crypto import Random


app = Flask(__name__)
client = MongoClient()
database = client.guvenlik


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/login')
def login():
    return database.users.find_one()['username']


def get_secure_passwd(passwd):
    salt = Random.new().read(32)  # 32 bit salt
    hash = SHA256.new()
    hash.update(salt + passwd.encode('utf8'))
    message = hash.digest()

    for i in range(1000):
        hash = SHA256.new()
        hash.update(message)
        message = hash.digest()

    return (salt, hash.digest())


if __name__ == '__main__':
    app.run(debug=True)
