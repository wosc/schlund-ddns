from flask import Flask, request
from ws.ddns.update import DNS
import os
import os.path
import wsgiref.handlers

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

app = Flask(__name__)


@app.route('/')
def update_view():
    config = ConfigParser({
        'url': 'https://gateway.schlundtech.de',
        'context': '10',
    })
    config.read(os.path.expanduser(
        os.environ.get('DDNS_CONFIG', '~/.schlund-ddns')))
    get = lambda x: config.get('default', x)

    try:
        get('username')
    except:
        raise RuntimeError('Not configured')

    hostname = request.args.get('hostname')
    ip = request.args.get('myip')

    if not (hostname and ip):
        raise RuntimeError('Required parameters: hostname, myip')

    dns = DNS(get('url'), get('username'), get('password'), get('context'))
    response = dns.update(hostname, ip)
    return str(response.result.status.find('text'))


@app.errorhandler(Exception)
def handle_error(error):
    return str(error), 500


def main():
    wsgiref.handlers.CGIHandler().run(app.wsgi_app)
