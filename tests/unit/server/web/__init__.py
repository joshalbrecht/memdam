
import unittest
import base64

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
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(app.config['USERNAME'] + ":" + app.config['PASSWORD'])
        }
