import flask

app = flask.Flask(__name__)

app.config.update(dict(
    DATABASE_FOLDER='/tmp/default.db',
    BLOB_URL='http://127.0.0.1/api/v1/blobs/',
    BLOBSTORE_FOLDER='/tmp',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
#load settings from the file defined by this variable
app.config.from_envvar('MEMDAM_SETTINGS', silent=True)
