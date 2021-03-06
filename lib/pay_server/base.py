import datetime
import decimal
from functools import partial
import json
import logging
import urllib

import requests

log = logging.getLogger('s.client')


class SolitudeError(Exception):
    pass


mapping = {
    'buyer': ['generic', 'buyer', ['get', 'post']],
    'buyer_paypal': ['paypal', 'buyer', ['get', 'post', 'patch', 'delete']],
    'seller': ['generic', 'seller', ['get', 'post']],
    'seller_paypal': ['paypal', 'seller', ['get', 'post', 'patch']],
    # PayPal API's
    'ipn': ['paypal', 'ipn', ['post']],
    'preapproval': ['paypal', 'preapproval', ['post', 'put', 'delete']],
    'pay': ['paypal', 'pay', ['post']],
    'pay_check': ['paypal', 'pay-check', ['post']],
    'permission_url': ['paypal', 'permission-url', ['post']],
    'refund': ['paypal', 'refund', ['post']],
}


class Encoder(json.JSONEncoder):

    date_format = '%Y-%m-%d'
    time_format = '%H:%M:%S'

    def default(self, v):
        """Encode some of our basic types in ways solitude understands."""
        if isinstance(v, datetime.datetime):
            return v.strftime("%s %s" % (self.date_format, self.time_format))
        elif isinstance(v, datetime.date):
            return v.strftime(self.date_format)
        elif isinstance(v, datetime.time):
            return v.strftime(self.time_format)
        elif isinstance(v, decimal.Decimal):
            return str(v)
        else:
            return super(Encoder, self).default(v)


class Client(object):

    def __init__(self, config=None):
        self.config = self.parse(config)
        self.encoder = None

    def _url(self, context, name, pk=None):
        url = '%s/%s/%s/' % (self.config['server'], context, name)
        if pk:
            url = '%s%s/' % (url, pk)
        return url

    def parse(self, config=None):
        config = {
            'server': config.get('server')
            # TODO: add in OAuth stuff.
        }
        return config

    def call(self, url, method, data=None):
        data = (json.dumps(data, cls=self.encoder or Encoder)
                if data else json.dumps({}))
        method = getattr(requests, method)
        result = method(url, data=data,
                        headers={'content-type': 'application/json'})

        if result.status_code in (200, 201, 202, 204):
            return json.loads(result.text) if result.text else {}
        else:
            data = ''
            try:
                data = json.loads(result.text) if result.text else {}
            except:
                log.error('Failed to parse error: %s' % result.text)
            raise SolitudeError(result.status_code, data)

    def __getattr__(self, attr):
        try:
            method, action = attr.split('_', 1)
        except:
            raise AttributeError(attr)

        target = mapping.get(action)
        if not target:
            raise AttributeError(attr)

        if method not in target[2]:
            raise AttributeError(attr)

        return partial(self.wrapped, **{'target': target, 'method': method})

    def wrapped(self, target=None, method=None, data=None, pk=None,
                filters=None):
        url = self._url(*target[:2], pk=pk)
        if filters:
            url = '%s?%s' % (url, urllib.urlencode(filters))
        return self.call(url, method, data=data)

