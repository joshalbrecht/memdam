
import nose.tools

import memdam.server.web.auth
import memdam.server.web_server
import memdam.server.admin

def test_server_auth():
    """
    Server is failing to return anything even though the user has been added to the database.
    """
    username = u"josh"
    password = u"password"
    memdam.server.web_server._parse_config(dict(DATABASE_FOLDER="/tmp/events"))
    memdam.server.admin.create_archive(username, password)
    nose.tools.eq_(memdam.server.web.auth.check_auth(username, password), True)
    
if __name__ == '__main__':
    test_server_auth()
    