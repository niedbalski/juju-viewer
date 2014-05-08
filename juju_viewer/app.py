import logging
import os
import gi
import yaml
import sys

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk

_HERE = os.path.abspath(os.path.dirname(__file__))


class MainWindowHandlers(object):

    def __init__(self, window):
        self.window = window

    def on_environments_changed(self, widget):
        (iterator, model) = (widget.get_active_iter(),
                             widget.get_model())

        environment = model[iterator][0]
        from jujuclient import Environment

        juju_env = Environment.connect(env=environment)
        print juju_env


class MainWindow(object):

    UI_DEFINITION_FILE = os.path.join(_HERE, 'ui', 'main.glade')
    DEFAULT_JUJU_ENV_FILE = os.path.expanduser("~/.juju/environments.yaml")

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.UI_DEFINITION_FILE)
        self.builder.connect_signals(MainWindowHandlers(self))

        self.setup_environments()
        self.window.show_all()

    @property
    def window(self):
        return self.builder.get_object("main")

    @property
    def environments(self):
        return self.builder.get_object("environments")

    def juju_environments(self):
        def is_juju_initiated():
            return os.path.exists(self.DEFAULT_JUJU_ENV_FILE)

        if not is_juju_initiated():
            return self.__error(
                "Juju has not been initiated yet, run juju init before")

        return yaml.load(open(
            self.DEFAULT_JUJU_ENV_FILE))

    def setup_environments(self):
        envs_store = Gtk.ListStore(str, str)
        for environment in self.juju_environments().get('environments').keys():
            envs_store.append([environment, environment])

        self.environments.set_model(envs_store)
        self.environments.set_entry_text_column(0)
        self.environments.set_active(0)


class Application(object):
    def __init__(self):
        self.w = MainWindow()

    def start(self):
        GLib.threads_init()
        Gdk.threads_init()
        Gdk.threads_enter()
        Gtk.main()
        Gdk.threads_leave()

    def quit_now(self, signum, frame):
        Gtk.main_quit()


def main(argv=None):
    if argv is None:
        argv = sys.argv

    import signal

    logging.basicConfig(level=logging.DEBUG)
    application = Application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    application.start()


if __name__ == '__main__':
    main()
