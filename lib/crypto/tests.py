# -*- coding: utf8 -*-
from django.conf import settings

import json
import mock
from nose.tools import eq_, raises

import amo.tests
from lib.crypto.receipt import sign, SigningError


@mock.patch('lib.metrics.urllib2.urlopen')
@mock.patch.object(settings, 'SIGNING_SERVER', 'http://localhost')
class TestReceipt(amo.tests.TestCase):

    def test_called(self, urlopen):
        urlopen.return_value = self.get_response(200)
        sign('my-receipt')
        eq_(urlopen.call_args[0][0].data, 'my-receipt')

    def test_some_unicode(self, urlopen):
        urlopen.return_value = self.get_response(200)
        sign({'name': u'Вагиф Сәмәдоғлу'})

    def get_response(self, code):
        response = mock.Mock()
        response.getcode = mock.Mock()
        response.getcode.return_value = code
        response.read.return_value = json.dumps({'receipt': ''})
        return response

    @raises(SigningError)
    def test_error(self, urlopen):
        urlopen.return_value = self.get_response(403)
        sign('x')

    def test_good(self, urlopen):
        urlopen.return_value = self.get_response(200)
        sign('x')

    @raises(SigningError)
    def test_other(self, urlopen):
        urlopen.return_value = self.get_response(206)
        sign('x')
