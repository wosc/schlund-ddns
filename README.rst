===============================
Schlundtech Dynamic DNS updater
===============================

This packages provides a way to update DNS records programmatically,
for customers of `Schlundtech`_, using their `XML-Gateway`_.

Many thanks to https://github.com/martinlowinski/php-dyndns for doing the heavy
lifting of figuring out how to talk to the XML-Gateway in a way that actually
makes it do what we want.

.. _`Schlundtech`: http://www.schlundtech.com/
.. _`XML-Gateway`: http://www.schlundtech.com/services/xml-gateway/


Usage
=====

First, you need to create a subdomain with an A-record in your domain, say ``home.example.com``, 
and install this package, e.g. with ``pip install ws.ddns`` (or ``git clone ...; pip install -e .``)

Then you can use the command-line utility provided by this package, like so::

    $ schlund-ddns --username USER --password PASS home.example.com 1.2.3.4

If you have both an A and AAAA record for the subdomain, you have to update them separately,
i.e. call the script twice, once with an IPv4 and a second time with IPv6 address.

(See ``schlund-ddns --help`` for more configuration parameters, e.g. the
``context`` that you were told to use when applying for the XML-Gateway.)

Instead of passing the parameters on the commandline, you can instead call ``schlund-ddns --config myconfig.ini`` (see below for the file format).


Alternatively, set up the provided cgi script ``schlund-ddns-cgi`` to provide
HTTP access. You'll need to provide username and password using a configuration
file and then passing that file's path as an environment variable. Here's an
example apache configuration snippet to do this::

    ScriptAlias /dns-update /path/to/ddns/schlund-ddns-cgi
    <Location /dns-update>
      SetEnv DDNS_CONFIG /path/to/ddns/config

      AuthName "Dynamic DNS"
      AuthType Basic
      AuthUserFile /path/to/ddns/htpasswd
      require valid-user
    </Location>

The configuration file is a standard ini file and should look like this::

    [default]
    username = USER
    password = PASS
    context  = CONTEXT

You can optionally add an ``allowed_hostnames = one.example.com two.example.com``
whitespace-separated list to the config file, only those will then be accepted.

The HTTP protocol is modeled after the one from `NoIP`_, that is, clients
should perform a request like this to trigger a DNS update::

    http://example.com/dns-update?hostname=home.example.com&myip=1.2.3.4


.. _`NoIP`: http://www.noip.com/integrate/request


There is also a docker image of the HTTP service here: https://hub.docker.com/r/customelements/schlund-ddns

2FA support
-----------

* Install ``pip install pyotp`` in addition to this package
* Pass the 2FA secret (probably 16 characters, you may have to reverse-engineer them from the QR-Code used for setup) as `--totp-secret`` commandline or configuration parameter
