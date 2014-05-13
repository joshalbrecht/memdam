import flask
import flask_bootstrap

app = flask.Flask(__name__)

flask_bootstrap.Bootstrap(app)

app.config.update(dict(
    DATABASE_FOLDER=':memory:',
    BLOBSTORE_FOLDER='/tmp',
    DEBUG=True,
    SECRET_KEY='development key',
    RUN_WSGI_SERVER=False,
    LISTEN_ADDRESS='127.0.0.1',
    LISTEN_PORT=5000,
    LOG_LEVEL='DEBUG',
))
#see web_server.py for the logic about which settings are overriden in which order
