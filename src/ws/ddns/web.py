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
    get = lambda x: config.get('default', x)  # noqa

    try:
        get('username')
    except Exception:
        raise RuntimeError('Not configured')

    hostname = request.args.get('hostname')
    ip = request.args.get('myip')

    if not (hostname and ip):
        raise RuntimeError('Required parameters: hostname, myip')

    if config.has_option('default', 'allowed_hostnames'):
        allowed = get('allowed_hostnames').split(' ')
        if hostname not in allowed:
            raise RuntimeError('Invalid hostname')

    dns = DNS(get('url'), get('username'), get('password'), get('context'))
    response = dns.update(hostname, ip)
    return str(response.result.status.find('text'))


@app.errorhandler(Exception)
def handle_error(error):
    return str(error), 500


def main():
    # We only have the one route
    os.environ['PATH_INFO'] = '/'
    wsgiref.handlers.CGIHandler().run(app.wsgi_app)
