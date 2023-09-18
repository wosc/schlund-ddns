from configparser import ConfigParser
import gocept.logging
import logging
import lxml.etree
import lxml.objectify
import requests
import ipaddress

try:
    import pyotp
except ImportError:  # soft dependency
    pyotp = None


log = logging.getLogger(__name__)

def serialize_xml(xml):
    lxml.objectify.deannotate(xml)
    lxml.etree.cleanup_namespaces(xml)
    xml = lxml.etree.tostring(xml, xml_declaration=True, pretty_print=True)
    return xml


class DNS(object):

    ZONE_INQUIRE = '0205'
    ZONE_UPDATE = '0202'

    def __init__(self, url, username, password, context, **kw):
        self.url = url
        self.username = username
        self.password = password
        self.context = context
        totp_secret = kw.get('totp_secret')
        if totp_secret is not None and pyotp is None:
            raise ValueError('Using totp_secret requires installing pytotp')
        self.totp_secret = totp_secret

    def post(self, xml):
        xml = serialize_xml(xml)
        log.debug('POST %s:\n%s', self.url, xml)
        response = requests.post(self.url, data=xml)
        return lxml.objectify.fromstring(response.text.encode('utf-8'))

    @property
    def _auth_xml(self):
        E = lxml.objectify.E
        auth = E.auth(
            E.user(self.username),
            E.password(self.password),
            E.context(self.context),
        )
        if self.totp_secret:
            auth.append(E.token(pyotp.TOTP(self.totp_secret).now()))
        return auth

    def get(self, domain):
        E = lxml.objectify.E
        query = E.request(
            self._auth_xml,
            E.task(
                E.code(self.ZONE_INQUIRE),
                E.zone(E.name(domain)),
            )
        )
        response = self.post(query)
        if not response.result.status.type == 'success':
            raise RuntimeError('Could not retrieve zone data: %s' %
                               response.result.status.find('text'))
        return response

    def update(self, hostname, ip):
        parts = hostname.split('.')
        host = '.'.join(parts[:-2])
        domain = '.'.join(parts[-2:])

        zone = self.get(domain).result.data.zone

        ip_obj = ipaddress.ip_address(ip)
        rtype = 'A' if isinstance(ip_obj, ipaddress.IPv4Address) else 'AAAA'

        current = zone.xpath('//rr[name = "%s" and type = "%s"]' % (host, rtype))
        if not current:
            raise ValueError('No entry for %s found in zone data' % hostname)
        current = current[0]
        current.value = ip

        for name in [
                'created', 'changed', 'domainsafe', 'owner', 'updated_by']:
            zone.remove(zone.find(name))

        E = lxml.objectify.E
        query = E.request(
            self._auth_xml,
            E.task(
                E.code(self.ZONE_UPDATE),
                zone,
            )
        )

        response = self.post(query)
        if not response.result.status.type == 'success':
            raise RuntimeError(
                'Could not update zone data:\n%s' % serialize_xml(response))
        return response


def main():
    parser = gocept.logging.ArgumentParser()
    parser.add_argument('--url', default='https://gateway.schlundtech.de',
                        help='URL of XML-Gateway')
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--context', default='10')
    parser.add_argument('--totp-secret')
    parser.add_argument('--config', help='configuration filename')
    parser.add_argument('hostname')
    parser.add_argument('ip')
    options = parser.parse_args()

    if options.config:
        config = ConfigParser({
            'url': 'https://gateway.schlundtech.de',
            'context': '10',
        })
        config.read(options.config)
        config = dict(config.items('default'))
    else:
        config = {x: getattr(options, x) for x in [
            'url', 'username', 'password', 'context', 'totp_secret']}

    dns = DNS(**config)
    response = dns.update(options.hostname, options.ip)
    log.info(response.result.status.find('text'))
