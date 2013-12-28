
from memdam.server.web import app

#register all of the blueprints (urls)
import memdam.server.web.blobs
import memdam.server.web.events
import memdam.server.web.queries

app.register_blueprint(memdam.server.web.blobs.blueprint, url_prefix='/api/v1/blobs')
app.register_blueprint(memdam.server.web.events.blueprint, url_prefix='/api/v1/events')
app.register_blueprint(memdam.server.web.queries.blueprint, url_prefix='/api/v1/queries')
