import threading

from gi.repository import GObject
from gi.repository import Gdk

from jujuclient import Environment


class ListMachinesThread(threading.Thread, GObject.GObject):

    __gsignals__ = {
        'on_status': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                      (GObject.TYPE_PYOBJECT, )),

        'on_status_error': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                            (GObject.TYPE_PYOBJECT, )),
    }

    def __init__(self, environment):
        threading.Thread.__init__(self)
        GObject.GObject.__init__(self)

        self.environment = environment

    def run(self):
        Gdk.threads_enter()
        try:
            env = Environment.connect(self.environment)
            self.emit('on_status',
                      env.status())

        except Exception as ex:
            self.emit('on_status_error', ex)
        finally:
            Gdk.threads_leave()


GObject.type_register(ListMachinesThread)