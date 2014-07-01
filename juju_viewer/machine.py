import gi
import os

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GdkPixbuf

_HERE = os.path.abspath(os.path.dirname(__file__))


class Machine(object):

    MACHINE_COLUMNS = {"Hardware": {'type': str},
                       "Life": {'type': str},
                       "Err": {'type': str},
                       "InstanceId": {
                           'type': str,
                           'index': 1,
                       },
                       "AgentState": {
                           "type": GdkPixbuf.Pixbuf,
                           "renderer": Gtk.CellRendererPixbuf(),
                           "index": 2,
                       },
                       "AgentStateInfo": {'type': str},
                       "DNSName": {
                           'type': str,
                           'index': 0,
                       },
                       "AgentVersion": {'type': str},
                       "Series": {'type': str},
                       "Id": {'type': str, "index": 0},
                       "Containers": {'type': str}}

    def __init__(self, data):
        for column in self.MACHINE_COLUMNS.keys():
            column_value = data.get(column, None)
            try:
                column_value = getattr(self, "transform_%s" % column.lower())(
                    column_value)
            except AttributeError:
                column_value = str(column_value)
            finally:
                setattr(self, column, column_value)

    def get_state_pixbuf(self, state):
        status_image_map = {
            'started': "state-green.png",
            'error': "state-red.png",
            'pending': "state-yellow.png",
            'down': "state-red.png",
        }

        fpath = os.path.join(_HERE, 'ui', 'pixmaps',
                             status_image_map.get(state,
                                                  'state-yellow.png'))

        return GdkPixbuf.Pixbuf.new_from_file(fpath)

    def transform_agentstate(self, value):
        return self.get_state_pixbuf(value)

    @classmethod
    def get_column_by_name(cls, name, index):
        renderer = cls.MACHINE_COLUMNS[name].get('renderer',
                                                 Gtk.CellRendererText())

        if isinstance(renderer, Gtk.CellRendererPixbuf):
            new_column = Gtk.TreeViewColumn(name)
            new_column.pack_start(renderer, expand=False)
            new_column.add_attribute(renderer, "pixbuf", index)
        else:
            new_column = Gtk.TreeViewColumn(name, renderer,
                                            text=index)
        new_column.set_name(name)
        return new_column

    @classmethod
    def get_column_types(cls):
        return map(lambda k: k[1]['type'],
                   sorted(cls.MACHINE_COLUMNS.items(),
                          key=lambda (k, v): v.get("index"), reverse=True))

    @classmethod
    def get_column_names(cls):
        """
        Returns the current column names ordered by the 'index' attribute
        """
        return map(lambda k: k[0],
                   sorted(cls.MACHINE_COLUMNS.items(),
                          key=lambda (k, v): v.get("index"), reverse=True))
