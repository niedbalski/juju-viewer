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
from gi.repository import GdkPixbuf

_HERE = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)

from juju import ListMachinesThread


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
        self.machines.set_size_request(200, 200)

        self.hydrate_environments()
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
    def environments(self):
        return self.builder.get_object("environments")

    def _get_state_pixbuf(self, state):
        status_image_map = {
            'started': "state-green.png",
            'error': "state-red.png",
            'pending': "state-yellow.png",
            'down': "state-red.png",
        }

        fpath = os.path.join(_HERE, 'ui', 'pixmaps',
                             status_image_map.get(state, 'error'))

        return GdkPixbuf.Pixbuf.new_from_file(fpath)

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
        self.environments.set_entry_text_column(0)
        self.environments.set_active(0)

    def on_status_error(self, e, v):
        print e, v

    def set_column_headers(self, machines):
        for machine in machines.values():
            i = 0
            for attr in machine.keys():
                column = Gtk.TreeViewColumn(attr)
                cell = Gtk.CellRendererText()
                column.pack_start(cell, False)
                column.add_attribute(cell, "text", i)
                self.machines.append_column(column)
                i = i + 1
            break

    def on_status(self, t, status):
        """
        Callback invoked when the machines list is updated
        """
        self.notebook.set_sensitive(True)

        machines = status.get('Machines', None)

        if not machines:
            #XXX: Handle this
            self.log.debug('No machines found')

        columns = self.machines.get_n_columns()

        if columns == 0:
            self.set_column_headers(machines)

        model = Gtk.ListStore(*([str for i in range(0,
                                 self.machines.get_n_columns())]))

        for machine in machines.values():
            row = []
            for attr, value in machine.items():
                if value in ('', {}):
                    value = None
                row.append(str(value))
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
