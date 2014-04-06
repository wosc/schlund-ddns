===============================
Schlundtech Dynamic DNS updater
===============================

This packages provides a way to update DNS records programmatically,
for customers of `Schlundtech`_, using their `XML-Gateway`_.

Many thanks to https://github.com/martinlowinski/php-dyndns for doing the heavy
lifting of figuring out how to talk to the XML-Gateway in a way that actually
makes it do what we want.

.. `Schlundtech`: http://www.schlundtech.com/
.. `XML-Gateway`: http://www.schlundtech.com/services/xml-gateway/


Usage
=====

First, you need to create a subdomain with an A-record in your domain, say
``home.example.com``.

Then you can use the command-line utility provided by this package, like so::

    $ schlund-ddns --username USER --password PASS home.example.com 1.2.3.4

(See ``ddns-update --help`` for more configuration parameters, e.g. the
``context`` that you were told to use when applying for the XML-Gateway.)
