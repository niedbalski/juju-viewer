import logging
import os
import gi
import yaml
import sys
import signal

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk

_HERE = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)

from juju import ListMachinesThread
from machine import Machine


class MainWindowHandlers(object):

    def __init__(self, window):
        self.window = window

    def on_environments_changed(self, widget):
        (iterator, model) = (widget.get_active_iter(),
                             widget.get_model())

        environment = model[iterator][0]
        if environment is None:
            raise Exception("Environment is not defined")

        t = ListMachinesThread(environment)
        t.connect("on_status", self.window.on_status)
        t.connect("on_status_error", self.window.on_status_error)
        t.start()


class MainWindow(object):

    UI_DEFINITION_FILE = os.path.join(_HERE, 'ui', 'main.glade')
    DEFAULT_JUJU_ENV_FILE = os.path.expanduser("~/.juju/environments.yaml")

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.UI_DEFINITION_FILE)
        self.builder.connect_signals(MainWindowHandlers(self))

        self.hydrate_environments()
        self.setup_machines_treeview()

        self.window.show_all()

    @property
    def window(self):
        return self.builder.get_object("main")

    @property
    def notebook(self):
        return self.builder.get_object("notebook")

    @property
    def machines(self):
        return self.builder.get_object("machines")

    @property
    def services(self):
        return self.builder.get_object("services")

    @property
    def environments(self):
        return self.builder.get_object("environments")

    def setup_services_treeview(self):
        for index, column_name in enumerate(Machine.get_column_names()):
            self.services.append_column(
                Machine.get_column_by_name(column_name, index))

    def setup_machines_treeview(self):
        for index, column_name in enumerate(Machine.get_column_names()):
            self.machines.append_column(
                Machine.get_column_by_name(column_name, index))

    def get_juju_environments(self):
        def is_juju_initiated():
            return os.path.exists(self.DEFAULT_JUJU_ENV_FILE)

        if not is_juju_initiated():
            return self.__error(
                "Juju has not been initiated yet, run 'juju init' before")

        return yaml.load(open(
            self.DEFAULT_JUJU_ENV_FILE))

    def hydrate_environments(self):
        """
        Hydrate the enviroments list store
        """
        envs_store = Gtk.ListStore(str, str)

        for environment in self.get_juju_environments().get(
                'environments').keys():
            envs_store.append([environment, environment])

        self.environments.set_model(envs_store)
        # self.environments.set_entry_text_column(0)
        # self.environments.set_active(0)

    def on_status_error(self, e, v):
        print e, v

    def on_status(self, t, machines):
        """
        Callback invoked when the machines list is updated
        """
        self.notebook.set_sensitive(True)
        model = Gtk.ListStore(*(Machine.get_column_types()))

        for machine in machines:
            row = []
            for column in Machine.get_column_names():
                row.append(getattr(machine, column))
            model.append(row)

        self.machines.set_model(model)


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

    logging.basicConfig(level=logging.DEBUG)

    application = Application()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    application.start()


if __name__ == '__main__':
    main()
