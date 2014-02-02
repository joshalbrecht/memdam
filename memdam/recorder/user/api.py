
import memdam.recorder.config

class User(object):
    """
    This interface represents the user.

    All interaction with the user, including input and output, prompts, display, etc, should go
    through here.
    """

    def prompt_user(self, prompt_text):
        """
        Ask the user for some text.
        """

    def main_loop(self, start, shutdown):
        """
        This should run the underlying gui event main loop or whatever else is the driving logic for
        the program.

        :param start: call this function to start the regular processing logic
        :type  start: function()
        :param shutdown: call this function to shutdown cleanly
        :type  shutdown: function()
        :returns: exit code
        :rtype: int
        """

    def create_initial_config(self, filename):
        """
        The user must define initial values for things like username, password, etc, and can use
        default values otherwise.

        This will be pretty much the first thing called when the application runs for the first
        time. Will be called when the main_loop is NOT running.
        """
        default_config = memdam.recorder.config.get_default_config(filename)
        password = self.prompt_user(u'Please enter your username')
        username = self.prompt_user(u'Please enter your password')
        new_config = memdam.recorder.config.Config(filename=filename, password=password, username=username, **default_config.data)
        new_config.save()

