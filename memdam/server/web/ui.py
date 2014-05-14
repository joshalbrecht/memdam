
import flask
from flask_wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField, IntegerField, FormField, validators
from wtforms.validators import Required


import memdam.common.query
import memdam.server.web.utils
import memdam.server.web.auth

blueprint = flask.Blueprint('ui', __name__)

# straight from the wtforms docs:
class TelephoneForm(Form):
    country_code = IntegerField('Country Code', [validators.required()])
    area_code = IntegerField('Area Code/Exchange', [validators.required()])
    number = TextField('Number')


class ExampleForm(Form):
    field1 = TextField('First Field', description='This is field one.')
    field2 = TextField('Second Field', description='This is field two.',
                       validators=[Required()])
    hidden_field = HiddenField('You cannot see this', description='Nope')
    radio_field = RadioField('This is a radio field', choices=[
        ('head_radio', 'Head radio'),
        ('radio_76fm', "Radio '76 FM"),
        ('lips_106', 'Lips 106'),
        ('wctr', 'WCTR'),
    ])
    checkbox_field = BooleanField('This is a checkbox',
                                  description='Checkboxes can be tricky.')

    # subforms
    mobile_phone = FormField(TelephoneForm)

    # you can change the label as well
    office_phone = FormField(TelephoneForm, label='Your office phone')

    submit_button = SubmitField('Submit Form')

    def validate_hidden_field(self, field):
        raise ValidationError('Always wrong')

@blueprint.route('', methods = ['GET', 'POST'])
@memdam.server.web.auth.requires_auth
def main_interface():
    """
    Return the HTML interface for interacting with the API from your browser
    """
    form = ExampleForm()
    form.validate_on_submit()
    return flask.render_template('index.html', name=flask.request.authorization.username, form=form)
