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

from mailanie import addressbook, config

class AddressBook(addressbook.AddressBook):
    def __init__(self):
        self.widget = gtk.ScrolledWindow()
        self.widget.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.pretty_label = gtk.HBox()
        self.pretty_label.set_spacing(3)
        self.pretty_label.pack_start(
            gtk.image_new_from_stock("address-book", gtk.ICON_SIZE_MENU),
            expand=False, fill=False)
        self.pretty_label.pack_start(gtk.Label(_("Address Book")))
        
        self.list_store = gtk.ListStore(object)
        self.list_view = gtk.TreeView(self.list_store)
        self.list_view.connect("button-press-event", self._button_press)
        self.list_model = self.list_view.get_model()

        self.list_view.set_headers_visible(False)
        self.widget.add(self.list_view)

        self.text_renderer = gtk.CellRendererText()
        self.text_column = gtk.TreeViewColumn(None, self.text_renderer)
        self.text_column.set_expand(True)
        self.list_view.append_column(self.text_column)
        self.text_column.set_cell_data_func(self.text_renderer,
                                            self._render_text)

        addressbook_folder = gio.File(config.get("path", "addressbook"))
        addressbook_path = addressbook_folder.get_path()

        super(AddressBook, self).__init__(addressbook_path)

        for person in self:
            self.list_store.append((person, ))

    def append(self, person):
        self.list_store.append((person, ))

    def _button_press(self, widget, event):
        if event.button == 1:
            x, y = int(event.x), int(event.y)
            widget_path = widget.get_path_at_pos(x, y)
            if widget_path:
                path, column, x, y = widget_path

    @staticmethod
    def _render_text(column, cell, model, iter):
        cell.set_property("text", model[iter][0]["fn"])
