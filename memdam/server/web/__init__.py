import flask

app = flask.Flask(__name__)

app.config.update(dict(
    DATABASE_FOLDER=':memory:',
    BLOBSTORE_FOLDER='/tmp',
    DEBUG=True,
    SECRET_KEY='development key',
    RUN_WSGI_SERVER=False
))
#see web_server.py for the logic about which settings are overriden in which order
