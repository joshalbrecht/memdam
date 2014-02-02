
import memdam.server.web.auth
import memdam.server.admin
import tests.unit.server.web

class AuthTest(tests.unit.server.web.FlaskResourceTestCase):
    def runTest(self):
        """Authentication succeeds when user is defined"""
        with self.context('/'):
            assert memdam.server.web.auth.check_auth(self.username, self.password)

if __name__ == '__main__':
    test = AuthTest()
    test.setUp()
    test.runTest()
