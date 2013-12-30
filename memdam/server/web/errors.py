
import werkzeug.exceptions
import flask

#class BadRequest(werkzeug.exceptions.BadRequest):
class BadRequest(Exception):
    """
    Overrides the description field with a more helpful message for specific errors.
    """
    def __init__(self, description):
        Exception.__init__(self, description)
        self.description = description

        #self.response = None
        #self.response = self.get_response(environ=flask.app.request.environ)

        self.code = 400
