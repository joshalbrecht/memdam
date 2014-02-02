
import unittest
import base64

import memdam.server.admin
from memdam.server.web.urls import app

class FlaskResourceTestCase(unittest.TestCase):
    """
    Base class for testing flask routes.
    Sets up archive and blobstore and auth.
    """

    def setUp(self):
        self.app = app
        app.config['DATABASE_FOLDER'] = ":memory:"
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.username = u'someguy'
        self.password = u'randopass'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(self.username + ":" + self.password)
        }

    def context(self, *args, **kwargs):
        return AuthenticationContext(self, *args, **kwargs)

class AuthenticationContext(object):

    def __init__(self, test_case, *args, **kwargs):
        self.test_case = test_case
        self.ctx = self.test_case.app.test_request_context(*args, **kwargs)

    def __enter__(self):
        result = self.ctx.__enter__()
        memdam.server.admin.create_archive(self.test_case.username, self.test_case.password)
        return result

    def __exit__(self, *args, **kwargs):
        result = self.ctx.__exit__(*args, **kwargs)
        return result
