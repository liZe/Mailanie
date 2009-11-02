# Mailanie - Cute Mailbox Explorator
# Copyright 2009 Guillaume Ayoub <guillaume.ayoub@kozea.fr>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

# Mailanie is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Mailanie.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import gio

from mailanie import maildir, config
from folder import Folder

class MailBox(maildir.MailBox):
    def __init__(self, path=None):
        if not path:
            folder = gio.File(config.get("path", "mailbox"))
            path = folder.get_path()

        super(MailBox, self).__init__(path)

        self.widget = gtk.ScrolledWindow()
        self.widget.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.tree_store = gtk.TreeStore(object)
        self.tree_view = gtk.TreeView(self.tree_store)
        self.tree_model = self.tree_view.get_model()

        self.tree_view.set_headers_visible(False)
        self.widget.add(self.tree_view)

        self.icon_renderer = gtk.CellRendererPixbuf()
        self.icon_column = gtk.TreeViewColumn(None, self.icon_renderer)
        self.tree_view.append_column(self.icon_column)
        self.icon_column.set_cell_data_func(self.icon_renderer,
                                            self.render_icon)

        self.text_renderer = gtk.CellRendererText()
        self.text_column = gtk.TreeViewColumn(None, self.text_renderer)
        self.tree_view.append_column(self.text_column)
        self.text_column.set_cell_data_func(self.text_renderer,
                                            self.render_text)

        self.tree_store.insert(None, 0, (Folder(self, "inbox"), ))

        for folder in self.list_folders():
            self.tree_store.append(None, (Folder(self, folder), ))

    @staticmethod
    def render_icon(column, cell, model, iter):
        folder = model[iter][0]
        cell.set_property("pixbuf", folder.pixbuf)

    @staticmethod
    def render_text(column, cell, model, iter):
        folder = model[iter][0]
        cell.set_property("text", folder.label)

    def list_boxes(self):
        return [row[0] for row in self.tree_store]
