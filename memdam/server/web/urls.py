
import traceback
import sys

import werkzeug.exceptions
import flask

import memdam
from memdam.server.web import app

#register all of the blueprints (urls)
import memdam.server.web.blobs
import memdam.server.web.events
import memdam.server.web.queries

app.register_blueprint(memdam.server.web.blobs.blueprint, url_prefix='/api/v1/blobs')
app.register_blueprint(memdam.server.web.events.blueprint, url_prefix='/api/v1/events')
app.register_blueprint(memdam.server.web.queries.blueprint, url_prefix='/api/v1/queries')

@app.errorhandler(Exception)
def handle_errors(err):
    """
    Generic JSON error handler. Adds a bit more color to what happened.
    """
    exc_info = sys.exc_info()
    trace_data = '\n'.join(traceback.format_exception(*exc_info))
    if isinstance(err, werkzeug.exceptions.HTTPException):
        response_data = dict(description=err.description)
        status_code = err.code
    else:
        response_data = dict(description=str(err))
        status_code = 500
    response_data['code'] = status_code
    response_data['failed'] = True
    response_data['trace'] = trace_data
    memdam.log.info("Request failed: " + str(response_data))
    return flask.make_response(flask.jsonify(response_data), status_code)
