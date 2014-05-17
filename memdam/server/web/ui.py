
import flask
from flask_wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, DateTimeField, validators
from wtforms.validators import Required

import memdam.common.query
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
    start_time = JSDateTimeField('Start', description='If specified, all events must occur at or after this time')
    end_time = JSDateTimeField('End', description='If specified, all events must occur before this time')
    namespace = TextField('Namespace', description='If specified, all events must be from this namespace')

@blueprint.route('', methods = ['GET', 'POST'])
@memdam.server.web.auth.requires_auth
def main_interface():
    """
    Return the HTML interface for interacting with the API from your browser
    """
    form = EventQueryForm()
    form.validate_on_submit()
    return flask.render_template('index.html', name=flask.request.authorization.username, form=form)
