
import werkzeug.exceptions

class BadRequest(werkzeug.exceptions.BadRequest):
    """
    Overrides the description field with a more helpful message for specific errors.
    """
    def __init__(self, description):
        self.description = description
