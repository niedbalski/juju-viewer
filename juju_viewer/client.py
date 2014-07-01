import threading

from gi.repository import GObject
from gi.repository import Gdk

from jujuclient import Environment
from machine import Machine

import yaml
import os
import logging

DEFAULT_JUJU_ENV_FILE = os.path.expanduser("~/.juju/environments.yaml")


logger = logging.getLogger(__name__)


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
                      (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT, )),

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

            self.emit('on_status', self.environment, results)

        except Exception as ex:
            self.emit('on_status_error', ex)
        finally:
            Gdk.threads_leave()


class AddMachinesThread(threading.Thread, GObject.GObject):

    __gsignals__ = {
        'on_machine_process': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                               (GObject.TYPE_PYOBJECT, )),

        'on_machine_complete': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                                (GObject.TYPE_PYOBJECT, )),

        'on_machine_error': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                             (GObject.TYPE_PYOBJECT, )),
    }

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        GObject.GObject.__init__(self)

        for k, v in kwargs.items():
            if k == 'callbacks':
                for name, callback in kwargs[k].items():
                    logger.debug("Added callback: %s to %s" % (name, __name__))
                    self.connect(name, callback)
            else:
                setattr(self, k, v)

        self.start()

    def on_machine_complete(self, *args, **kwargs):
        self.emit("on_machine_complete", args)

    def on_machine_process(self, *args, **kwargs):
        self.emit("on_machine_process", args)

    def run(self):
        Gdk.threads_enter()
        try:
            env = Environment.connect(self.environment)
            r = env.add_machine(series=self.series,
                                constraints=self.constraints)

            machine_id = r.get('Machine')
            logger.debug(
                "Threaded watcher for id:%s on %s" % (machine_id, __name__))

            threading.Thread(target=env.wait_for_machines,
                             args=(machine_id, ),
                             kwargs={
                                 'callbacks': {
                                     'on_complete': self.on_machine_complete,
                                     'on_process': self.on_machine_process,
                                 }
                             }).start()

        except Exception as ex:
            self.emit('on_machine_error', ex)
        finally:
            Gdk.threads_leave()


GObject.type_register(ListMachinesThread)
