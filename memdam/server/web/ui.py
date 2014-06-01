
import json

import flask
from flask_wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, DateTimeField, validators
from wtforms.validators import Required

import memdam.common.query
import memdam.eventstore.sqlite
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('ui', __name__)

class JSDateTimeField(DateTimeField):
    def __call__(self, **kwargs):
        result = DateTimeField.__call__(self, **kwargs)
        result += '''
<input type="button" id="'''+self.id+'''_clear" value="Clear"/>
<script>
    $("#'''+self.id+'''").AnyTime_picker( {
      format: "%Y-%m-%d %H:%i:%s %:",
      formatUtcOffset: "%: (%@)" } );
    $("#'''+self.id+'''_clear").click( function(e) {
      $("#'''+self.id+'''").val("").change(); }
    );
</script>
        '''
        return result

class EventQueryForm(Form):
    start_time = JSDateTimeField('Start', validators=[validators.optional()], description='If specified, all events must occur at or after this time')
    end_time = JSDateTimeField('End', validators=[validators.optional()], description='If specified, all events must occur before this time')
    namespace = TextField('Namespace', description='If specified, all events must be from this namespace')
    submit = SubmitField('Submit')

def _make_query(start, end, namespace):
    filters = []
    if namespace is not None:
        filters.append(memdam.common.query.QueryFilter('namespace__namespace', '=', namespace))
    if start is not None:
        filters.append(memdam.common.query.QueryFilter('time__time', '>=', memdam.eventstore.sqlite.convert_time_to_long(start)))
    if end is not None:
        filters.append(memdam.common.query.QueryFilter('time__time', '<', memdam.eventstore.sqlite.convert_time_to_long(end)))
    return memdam.common.query.Query(filters=tuple(filters))

@blueprint.route('', methods = ['GET', 'POST'])
@memdam.server.web.auth.requires_auth
def main_interface():
    """
    Return the HTML interface for interacting with the API from your browser
    """
    form = EventQueryForm()
    events = {}
    if form.validate_on_submit():
        start = form.start_time.data
        end = form.end_time.data
        namespace = form.namespace.data
        if namespace == u'':
            namespace = None
        query = _make_query(start, end, namespace)
        archive = memdam.server.web.utils.get_archive(flask.request.authorization.username)
        events = archive.find(query)
        events = sorted(events, key=lambda x: x.time__time)
    return flask.render_template('index.html', name=flask.request.authorization.username, form=form, events=events, json=json)
