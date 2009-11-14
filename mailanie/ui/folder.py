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
import pango
import os
import time

from mailanie import folder, config
import mail

class Folder(folder.Folder):
    _labels = (
        "inbox",
        "sent",
        "junk",
        "draft",
        "trash",
        )

    def __init__(self, mailbox, label):
        super(Folder, self).__init__(mailbox, label)

        if label in self._labels:
            self.label = gtk.stock_lookup(label)[1]
            self.pixbuf = \
                 gtk.Window().render_icon(label, gtk.ICON_SIZE_SMALL_TOOLBAR)
        else:
            self.label = label
            self.pixbuf = \
                gtk.Window().render_icon("folder", gtk.ICON_SIZE_SMALL_TOOLBAR)

        self.widget = gtk.VBox()
        self.widget.filter = self.filter

        self.progress = gtk.ProgressBar()

        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.widget.add(self.scrolled)

        self.list_store = gtk.ListStore(object)
        self.list_view = gtk.TreeView(self.list_store)
        self.list_view.connect("button-press-event", self._button_press)
        self.list_model = self.list_view.get_model()

        self.list_view.set_headers_visible(False)
        self.list_view.set_rules_hint(True)
        self.scrolled.add(self.list_view)

        self.status_renderer = gtk.CellRendererPixbuf()
        self.status_renderer.set_property("stock-size", gtk.ICON_SIZE_MENU)
        self.status_column = gtk.TreeViewColumn(None, self.status_renderer)
        self.status_column.set_expand(False)
        self.list_view.append_column(self.status_column)
        self.status_column.set_cell_data_func(self.status_renderer,
                                              self._render_status)

        self.text_renderer = gtk.CellRendererText()
        self.text_renderer.props.ellipsize = pango.ELLIPSIZE_END
        self.text_column = gtk.TreeViewColumn(None, self.text_renderer)
        self.text_column.set_expand(True)
        self.list_view.append_column(self.text_column)
        self.text_column.set_cell_data_func(self.text_renderer,
                                            self._render_text,
                                            self._address)

        self.date_renderer = gtk.CellRendererText()
        self.date_column = gtk.TreeViewColumn(None, self.date_renderer)
        self.date_column.set_expand(False)
        self.list_view.append_column(self.date_column)
        self.date_column.set_cell_data_func(self.date_renderer,
                                            self._render_date)
        self.date_renderer.set_property("alignment", pango.ALIGN_RIGHT)
        self.date_renderer.set_property("xalign", 1)

        self.trash_renderer = gtk.CellRendererPixbuf()
        self.trash_renderer.set_property("stock-id", "delete")
        self.trash_renderer.set_property("stock-size", gtk.ICON_SIZE_MENU)
        self.trash_column = gtk.TreeViewColumn(None, self.trash_renderer)
        self.trash_column.set_expand(False)
        self.list_view.append_column(self.trash_column)

        self.pretty_label = gtk.HBox()
        self.pretty_label.set_spacing(3)
        self.pretty_label.pack_start(
            gtk.image_new_from_pixbuf(self.pixbuf), False, False)
        self.pretty_label.pack_start(gtk.Label(self.label))

    def show_progress(self, visible):
        shown = self.progress in self.widget.get_children()
        if visible:
            if not shown:
                self.widget.pack_start(self.progress, False)
        else:
            if shown:
                self.widget.remove(self.progress)
        self.progress.show()

    def load(self):
        if self._loaded:
            return

        name = str(abs(hash(self.mailbox._path)))
        cache_file = gio.File(config.get("path", "folder"))
        cache_path = os.path.join(cache_file.get_path(), name)

        super(Folder, self).load(cache_path)

        for i, new_mail in enumerate(self._headers):
            headers = mail.MailHeaders(
                new_mail.get_key(),
                new_mail.get_header("Subject"),
                new_mail.get_header("Address"),
                new_mail.get_header("Date"),
                new_mail.get_flags(),
                new_mail.get_header("Copie"))
            self._headers[i] = headers
            self.list_store.append((headers, ))

        self.list_store.set_default_sort_func(self._compare)
        self.list_store.set_sort_column_id(-1, gtk.SORT_DESCENDING)

    def filter(self, string=""):
        filter_model = self.list_store.filter_new()
        filter_model.set_visible_func(self._filter, string)
        self.list_view.set_model(filter_model)

    @staticmethod
    def _filter(model, iter, string):
        filter_string = u"\n".join((
                u" ".join(
                    " ".join(model[iter][0].get_header("Address"))),
                model[iter][0].get_header("Subject"))).lower()
        return string.lower() in filter_string

    def update(self):
        update = super(Folder, self).update()

        if not self._loaded or not update:
            return []

        self.progress.set_fraction(0)
        self.progress.set_text(_("Loading %s") % self.label)
        self.show_progress(True)

        while gtk.events_pending():
            gtk.main_iteration(False)

        for progress in update:
            self.progress.set_fraction(progress)
            self.progress.set_text("%i %%" % (progress * 100))
            while gtk.events_pending():
                gtk.main_iteration(False)
            if progress == 1:
                self.show_progress(False)
                old_keys, new_keys = update.next()

        old_iters = []
        row_iter = self.list_store.get_iter_root()
        while row_iter:
            if self.list_store.get_value(row_iter, 0).get_key() in old_keys:
                old_iters.append(row_iter)
            row_iter = self.list_store.iter_next(row_iter)
        for iter in old_iters:
            self.list_store.remove(iter)

        new_mails = []
        for i, new_mail in enumerate(self._headers):
            if new_mail.get_key() in new_keys:
                headers = mail.MailHeaders(
                    new_mail.get_key(),
                    new_mail.get_header("Subject"),
                    new_mail.get_header("Address"),
                    new_mail.get_header("Date"),
                    new_mail.get_flags(),
                    new_mail.get_header("Copie"))
                self._headers[i] = headers
                new_mails.append(headers)
                self.list_store.append((headers, ))

        if new_mails:
            while gtk.events_pending():
                gtk.main_iteration(False)

            self.list_view.scroll_to_point(0, 0)

        return new_mails

    def delete_trash_mails(self):
        delete = super(Folder, self).delete_trash_mails()

        if not self._loaded or not delete:
            return []

        self.progress.set_fraction(0)
        self.progress.set_text(_("Deleting Mails in %s") % self.label)
        self.show_progress(True)

        while gtk.events_pending():
            gtk.main_iteration(False)

        for progress in delete:
            self.progress.set_fraction(progress)
            self.progress.set_text("%i %%" % (progress * 100))
            while gtk.events_pending():
                gtk.main_iteration(False)
            if progress == 1:
                self.show_progress(False)
                deleted_keys = delete.next()

        deleted_iters = []
        row_iter = self.list_store.get_iter_root()
        while row_iter:
            if self.list_store.get_value(row_iter, 0).get_key() in deleted_keys:
                deleted_iters.append(row_iter)
            row_iter = self.list_store.iter_next(row_iter)
        for iter in deleted_iters:
            self.list_store.remove(iter)

    def _button_press(self, widget, event):
        if event.button == 1:
            x, y = int(event.x), int(event.y)
            widget_path = widget.get_path_at_pos(x, y)
            if widget_path:
                path, column, x, y = widget_path
                if column == self.status_column:
                    header = self.list_model[path][0]
                    if "S" in header.get_flags():
                        header.remove_flag("S")
                    else:
                        header.add_flag("S")
                    self.update_info(
                        header.get_key(), header.get_info())
                    self.list_view.queue_draw()
                    return True
                elif column == self.trash_column:
                    header = self.list_model[path][0]
                    if "T" in header.get_flags():
                        header.remove_flag("T")
                    else:
                        header.add_flag("T")
                    self.update_info(
                        header.get_key(), header.get_info())
                    self.list_view.queue_draw()
                    return True

    @staticmethod
    def _render_status(column, cell, model, iter):
        flags = model[iter][0].get_flags()
        if "T" in flags:
            cell.set_property("stock-id", "trash")
        else:
            if "S" in flags:
                if "R" in flags:
                    cell.set_property("stock-id", "replied")
                elif "F" in flags:
                    cell.set_property("stock-id", "forwardev")
                else:
                    cell.set_property("stock-id", "read")
            else:
                cell.set_property("stock-id", "unread")

    @staticmethod
    def _render_text(column, cell, model, iter, address="From"):
        subject = model[iter][0].get_header("Subject") or "[%s]" % _("Untitled")
        subject = u" ".join(subject.split())
        subject = subject.replace("&", "&amp;").replace("<", "&lt;")
        addresses = model[iter][0].get_header("Address")
        addresses = [address[0] or address[1] for address in addresses]
        addresses = [address.replace("&", "&amp;").replace("<", "&lt;")
                     for address in addresses]
        copies = model[iter][0].get_header("Copie")
        copies = [address[0] or address[1] for address in copies]
        copies = [address.replace("&", "&amp;").replace("<", "&lt;")
                     for address in copies]
        all_addresses = ", ".join(addresses) or _("Unknown")
        if copies:
            all_addresses += " (+ %s)" % ", ".join(copies)
        cell.set_property("markup",
                          "<big><b>%s</b></big>\n" % subject +
                          "<i>%s</i>" % all_addresses)

        if "T" in model[iter][0].get_flags():
            cell.set_property("foreground", "#AA0000")
        elif "S" not in model[iter][0].get_flags():
            cell.set_property("foreground", "#00AA00")
        else:
            cell.set_property("foreground", None)

    @staticmethod
    def _render_date(column, cell, model, iter):
        date = time.localtime(model[iter][0].get_header("Date"))
        cell.set_property("text", time.strftime("%-d %b %y\n%H:%M", date))

    @staticmethod
    def _compare(tree_model, iter1, iter2):
        if tree_model[iter1][0].get_header("Date") > \
                tree_model[iter2][0].get_header("Date"):
            return 1
        else:
            return -1
