import gocept.logging
import logging
import lxml.etree
import lxml.objectify
import requests


log = logging.getLogger(__name__)


def serialize_xml(xml):
    lxml.objectify.deannotate(xml)
    lxml.etree.cleanup_namespaces(xml)
    xml = lxml.etree.tostring(xml, xml_declaration=True, pretty_print=True)
    return xml


class DNS(object):

    ZONE_INQUIRE = '0205'
    ZONE_UPDATE = '0202'

    def __init__(self, url, username, password, context):
        self.url = url
        self.username = username
        self.password = password
        self.context = context

    def post(self, xml):
        xml = serialize_xml(xml)
        log.debug('POST %s:\n%s', self.url, xml)
        response = requests.post(self.url, data=xml)
        return lxml.objectify.fromstring(response.text.encode('utf-8'))

    @property
    def _auth_xml(self):
        E = lxml.objectify.E
        return E.auth(
            E.user(self.username),
            E.password(self.password),
            E.context(self.context),
        )

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
        host, domain = hostname.split('.', 1)
        zone = self.get(domain).result.data.zone

        current = zone.xpath('//rr[name = "%s"]' % host)
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
    parser.add_argument('hostname')
    parser.add_argument('ip')
    options = parser.parse_args()
    dns = DNS(options.url, options.username, options.password, options.context)
    response = dns.update(options.hostname, options.ip)
    print(response.result.status.find('text'))
