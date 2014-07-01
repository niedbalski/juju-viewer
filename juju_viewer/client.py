import threading

from gi.repository import GObject
from gi.repository import Gdk

from jujuclient import Environment
from machine import Machine

import yaml
import os

DEFAULT_JUJU_ENV_FILE = os.path.expanduser("~/.juju/environments.yaml")


def is_juju_initiated(env_path):
    return os.path.exists(env_path)


def get_environments(env_path=None):
    if not env_path:
        env_path = DEFAULT_JUJU_ENV_FILE
    if not is_juju_initiated(env_path):
        raise Exception(
            "Juju has not been initiated yet, run 'juju init' before")

    return yaml.load(open(env_path))


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

            status = env.status()
            machines = status.get('Machines', None).values()
            results = []
            for machine in machines:
                results.append(Machine(machine))

            self.emit('on_status', results)

        except Exception as ex:
            self.emit('on_status_error', ex)
        finally:
            Gdk.threads_leave()


GObject.type_register(ListMachinesThread)
