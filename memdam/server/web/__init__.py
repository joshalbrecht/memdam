import flask

app = flask.Flask(__name__)

app.config.update(dict(
    DATABASE='/tmp/default.db',
    BLOB_URL='http://127.0.0.1/api/v1/blobs/',
    BLOBSTORE_FOLDER='/tmp',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
#load settings from the file defined by this variable
app.config.from_envvar('MEMDAM_SETTINGS', silent=True)

#register all of the blueprints (urls)
import memdam.server.web.blobs
import memdam.server.web.events
import memdam.server.web.queries

app.register_blueprint(memdam.server.web.blobs.blueprint, url_prefix='/api/v1/blobs')
app.register_blueprint(memdam.server.web.events.blueprint, url_prefix='/api/v1/events')
app.register_blueprint(memdam.server.web.queries.blueprint, url_prefix='/api/v1/queries')
