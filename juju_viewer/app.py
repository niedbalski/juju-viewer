import logging
import os
import gi
import sys
import signal

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gdk

_HERE = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)

from juju_viewer.machine import Machine
from juju_viewer.client import (
    ListMachinesThread,
    AddMachinesThread,
    get_environments)


class MainWindowHandlers(object):

    def __init__(self, window):
        self.window = window

    def on_environments_refresh_clicked(self, widget):
        self.window.setup_environments()

    def on_add_machine_clicked(self, widget):
        self.window.add_machine.show()

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


class AddMachineWindow(object):

    DEFAULT_SERIES = ('trusty', 'precise', )

    def __init__(self, parent):
        self.parent = parent
        self.builder = self.parent.builder

        self.setup_series()
        self.series.connect("changed", self.on_series_changed)

        self.apply_btn.connect("clicked", self.on_apply_btn_clicked)
        self.cancel_btn.connect("clicked", self.on_cancel_btn_clicked)

    @property
    def window(self):
        return self.builder.get_object("add_machine_dialog")

    @property
    def cancel_btn(self):
        return self.builder.get_object("add_machine_cancel_btn")

    @property
    def apply_btn(self):
        return self.builder.get_object("add_machine_apply_btn")

    @property
    def series(self):
        return self.builder.get_object("machine_series")

    @property
    def constraints(self):
        return self.builder.get_object("machine_constraints")

    def on_series_changed(self, widget):
        (iterator, model) = (widget.get_active_iter(),
                             widget.get_model())
        series = model[iterator][0]
        if series:
            self.apply_btn.set_sensitive(True)
        else:
            self.apply_btn.set_sensitive(False)
        self.selected_series = series

    def _prepare_constraints(self, value):
        if value in ('',):
            value = None
        #XXX: parse memory=8G,cpus=2
        return value

    def on_apply_btn_clicked(self, widget):
        """On apply, start a AddMachinesThread instance
        """
        AddMachinesThread(
            environment=self.parent.selected_environment,
            constraints=self._prepare_constraints(
                self.constraints.get_text()),
            series=self.selected_series,
            callbacks={
                'on_machine_complete': self.on_machine_complete,
                'on_machine_process': self.on_machine_process,
                'on_machine_error': self.parent.on_status_error
            })

        self.window.hide()

    def on_machine_process(self, t, args):
        print args

    def on_machine_complete(self, t, args):
        print args

    def on_cancel_btn_clicked(self, widget):
        self.window.hide()

    def show(self):
        self.window.show()

    def setup_series(self):
        """Hydrate the series list store
        """
        series_store = Gtk.ListStore(str, str)
        for series in self.DEFAULT_SERIES:
            series_store.append([series, series])

        self.series.set_model(series_store)


class MainWindow(object):

    UI_DEFINITION_FILE = os.path.join(_HERE, 'ui', 'main.glade')

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.UI_DEFINITION_FILE)
        self.builder.connect_signals(MainWindowHandlers(self))

        self.setup_environments()

        self.setup_machines_treeview()
        self.setup_services_treeview()

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
    def add_machine(self):
        try:
            return self._add_machine
        except AttributeError:
            self._add_machine = AddMachineWindow(self)
        return self._add_machine

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

    def setup_environments(self):
        """Hydrate the enviroments list store
        """
        envs_store = Gtk.ListStore(str, str)

        logger.info("Updating enviroments")
        for environment in get_environments().get('environments').keys():
            envs_store.append([environment, environment])
            logger.info("Added environment: %s" % environment)
        self.environments.set_model(envs_store)

    def on_progress_update(self, value):
        print "Creating machine: %s" % value

    def on_status_error(self, e, v):
        print e, v

    def on_status(self, t, environment, machines):
        """Callback invoked when the machines list is updated
        """
        self.notebook.set_sensitive(True)

        model = Gtk.ListStore(*(Machine.get_column_types()))
        for machine in machines:
            row = []
            for column in Machine.get_column_names():
                row.append(getattr(machine, column))
            model.append(row)

        self.machines.set_model(model)
        self.selected_environment = environment


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
