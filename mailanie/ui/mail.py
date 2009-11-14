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
import pango
import gio
import os
import email

from mailanie import config, mail

_translated_headers = [_("Subject"), _("From"), _("To"), _("Cc"), _("Bcc")]



class MailHeaders(mail.MailHeaders):
    def get_mail(self, mailbox):
        if not self._mail:
            headers_mail = super(MailHeaders, self).get_mail(mailbox)
            
            self._mail = ReadMail(headers_mail.message,
                                  headers_mail.key)
        return self._mail



class Mail(mail.Mail):
    def load(self):
        if self._loaded:
            return

        folder = self.key
        cache_file = gio.File(config.get("path", "part"))
        cache_path = os.path.join(cache_file.get_path(), folder)

        super(Mail, self).load(cache_path)

        self.widget = gtk.VBox()
        self.widget.set_spacing(1)

        self.text_buffer = gtk.TextBuffer()
        self.text_view = gtk.TextView(self.text_buffer)
        self.text_view.set_wrap_mode(gtk.WRAP_WORD)
        self.text_view.set_left_margin(2)
        self.text_view.set_right_margin(2)

        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scrolled.set_size_request(0, -1)
        self.scrolled.add(self.text_view)

        self.pretty_label = gtk.HBox()
        self.pretty_label.set_spacing(3)
        mail_image = gtk.image_new_from_stock(
            "mail", gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.pretty_label.pack_start(mail_image, expand=False)
        self.subject_label = gtk.Label(self.label)
        self.pretty_label.pack_start(self.subject_label)

        self.widget.pack_start(self.scrolled)

        self.list_store = gtk.ListStore(object)
        self.list_view = gtk.TreeView(self.list_store)
        self.list_view.connect("row-activated", self.open_part)
        self.list_model = self.list_view.get_model()

        self.list_view.set_headers_visible(False)
        self.widget.pack_start(self.list_view, expand=False)

        self.icon_renderer = gtk.CellRendererPixbuf()
        self.icon_column = gtk.TreeViewColumn(None, self.icon_renderer)
        self.icon_column.set_expand(False)
        self.list_view.append_column(self.icon_column)
        self.icon_column.set_cell_data_func(self.icon_renderer,
                                            self._render_icon)

        self.title_renderer = gtk.CellRendererText()
        self.title_renderer.props.ellipsize = pango.ELLIPSIZE_END
        self.title_column = gtk.TreeViewColumn(None, self.title_renderer)
        self.title_column.set_expand(True)
        self.list_view.append_column(self.title_column)
        self.title_column.set_cell_data_func(self.title_renderer,
                                             self._render_title)

        text = u""
        for part in self.walk():
            coding = part.get_content_charset("latin-1")
            mimetype = part.get_content_type()
            message = part.get_payload(decode=True)
            name = part.get_filename()

            if message:
                try:
                    message = message.decode(coding)
                except:
                    message = message.decode("latin-1")

                if mimetype == "text/plain":
                    text += message
                else:
                    self.list_store.append(
                        (Part(message, name, mimetype, coding, self.key), ))

        self.text_buffer.set_text(text)

    @staticmethod
    def _render_icon(column, cell, model, iter):
        icon_name = model[iter][0].icon_name
        if icon_name:
            icon_theme = gtk.icon_theme_get_default()
            icon_size = gtk.icon_size_lookup(gtk.ICON_SIZE_MENU)[0]
            icon = icon_theme.load_icon(icon_name, icon_size, 0)
            cell.set_property("pixbuf", icon)
        else:
            cell.set_property("pixbuf", None)

    @staticmethod
    def _render_title(column, cell, model, iter):
        title = model[iter][0].name
        cell.set_property("text", title)

    def open_part(self, tree_view, path, view_column):
        part = tree_view.get_model()[path][0]
        part.open()



class ReadMail(Mail, mail.ReadMail):
    def load(self):
        if self._loaded:
            return

        super(ReadMail, self).load()

        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)

        self.top_box = gtk.HBox()
        self.top_box.set_border_width(2)

        headers = self.get_headers()
        subject = headers.get_header("Subject") or "[%s]" % _("Untitled")
        subject = subject.replace("&", "&amp;").replace("<", "&lt;")
        addresses = headers.get_header("Address")
        addresses = [address[0] or address[1] for address in addresses]
        addresses = [address.replace("&", "&amp;").replace("<", "&lt;")
                     for address in addresses]
        copies = headers.get_header("Copie")
        copies = [address[0] or address[1] for address in copies]
        copies = [address.replace("&", "&amp;").replace("<", "&lt;")
                     for address in copies]
        all_addresses = ", ".join(addresses) or _("Unknown")
        if copies:
            all_addresses += " (+ %s)" % ", ".join(copies)
        self.header_label = gtk.Label("<big><b>%s</b></big>\n" % subject +
                                      "<i>%s</i>" % all_addresses)
        self.header_label.props.ellipsize = pango.ELLIPSIZE_END
        self.header_label.set_alignment(0, 0.5)
        self.header_label.set_use_markup(True)
        self.top_box.pack_start(self.header_label)

        self.button_box = gtk.HBox()
        self.button_alignment = gtk.Alignment()
        self.button_alignment.add(self.button_box)

        self.reply_button = gtk.Button()
        mail_reply_image = gtk.image_new_from_stock(
            "mail-reply", gtk.ICON_SIZE_BUTTON)
        self.reply_button.set_image(mail_reply_image)
        self.button_box.pack_start(self.reply_button, expand=False)

        self.reply_all_button = gtk.Button()
        mail_reply_all_image = gtk.image_new_from_stock(
            "mail-reply-all", gtk.ICON_SIZE_BUTTON)
        self.reply_all_button.set_image(mail_reply_all_image)
        self.button_box.pack_start(self.reply_all_button, expand=False)

        self.forward_button = gtk.Button()
        mail_forward_image = gtk.image_new_from_stock(
            "mail-forward", gtk.ICON_SIZE_BUTTON)
        self.forward_button.set_image(mail_forward_image)
        self.button_box.pack_start(self.forward_button, expand=False)

        self.top_box.pack_end(self.button_alignment, expand=False)

        self.widget.pack_start(self.top_box, expand=False)
        self.widget.reorder_child(self.top_box, 0)



class WriteMail(Mail, mail.WriteMail):
    def load(self):
        if self._loaded:
            return

        super(WriteMail, self).load()

        self._addresses = {}

        self.label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.entry_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        self.top_box = gtk.HBox()
        self.top_box.set_border_width(2)
        self.top_box.set_spacing(2)

        self.header_box = gtk.VBox()
        self.header_box.set_spacing(1)
        self.top_box.pack_start(self.header_box)

        label, entry = self._add_line("Subject")
        entry.connect("changed",
                      lambda cell: self._update_subject(cell.get_text()))
        self._add_line("To")

        self.button_box = gtk.HBox()
        self.button_alignment = gtk.Alignment()
        self.button_alignment.add(self.button_box)

        self.draft_button = gtk.Button()
        mail_draft_image = gtk.image_new_from_stock(
            "draft", gtk.ICON_SIZE_BUTTON)
        self.draft_button.set_image(mail_draft_image)
        self.button_box.pack_start(self.draft_button, expand=False)

        self.send_button = gtk.Button()
        mail_send_image = gtk.image_new_from_stock(
            "mail-send", gtk.ICON_SIZE_BUTTON)
        self.send_button.set_image(mail_send_image)
        self.button_box.pack_start(self.send_button, expand=False)

        self.top_box.pack_end(self.button_alignment, expand=False)

        self.widget.pack_start(self.top_box, expand=False)
        self.widget.reorder_child(self.top_box, 0)

    def send(self):
        self.set_type("text/plain")

        self.message = self.text_buffer.props.text
        self.set_payload(self.message.encode("utf-8"), "utf-8")

        del self["Subject"]
        self["Subject"] = email.header.Header(self.label.encode("utf-8"), "utf-8").encode()

        for header, entries in self._addresses.items():
            del self[header]
            for entry in entries:
                name, address = email.utils.parseaddr(entry.get_text().encode("utf-8"))
                if name:
                    name = email.header.Header(name, "utf-8").encode()
                    self[header] = email.utils.formataddr((name, address))
                else:
                    self[header] = address

        super(WriteMail, self).send()

    def _add_line(self, title):
        line = gtk.HBox()
        line.set_spacing(5)
        line.key = title

        line.label = gtk.Label(_(title))
        self.label_group.add_widget(line.label)
        line.label.set_alignment(1, 0.5)
        line.pack_start(line.label, expand=False)

        line.entry = gtk.Entry()
        self.entry_group.add_widget(line.entry)
        line.pack_start(line.entry)

        if title in self:
            line.entry.set_text(mail.decode(self[title]))

        self.header_box.pack_start(line)

        if title not in ("Subject", ):
            line.entry.connect("key-press-event", lambda widget, event:
                              self._check_address(event.string, line))
            line.entry.connect("backspace", lambda widget:
                              self._backspace_address(widget.get_text(), line))
            line.entry.connect("activate", lambda widget:
                              self.text_view.grab_focus())

            if line.key not in self._addresses:
                self._addresses[line.key] = []
            self._addresses[line.key].append(line.entry)

        line.show_all()

        return line

    def _remove_line(self, line):
        header_lines = self.header_box.get_children()
        if len(header_lines) <= 2:
            return

        position = header_lines.index(line)

        self.label_group.remove_widget(line.label)
        self.entry_group.remove_widget(line.entry)
        self._addresses[line.key].remove(line.entry)
        self.header_box.remove(line)

        focus_entry = header_lines[position - 1].entry
        focus_entry.grab_focus()
        focus_entry.set_position(-1)

    def _backspace_address(self, full_string, line):
        if not full_string:
            self._remove_line(line)

    def _check_address(self, character, line):
        if character == ",":
            label, entry = self._add_line("To")
            entry.grab_focus()
            return True

    def _update_subject(self, subject):
        self.label = subject or "[%s]" % _("Untitled")
        self.subject_label.set_text(self.label)



class Part(object):
    def __init__(self, message, name, mimetype, coding, key):
        self.message = message
        self.name = name or "[%s]" % _("Untitled")

        part_folder = gio.File(config.get("path", "part"))
        path = part_folder.get_path()
        folder = key
        filename = os.path.join(path, folder, self.name)

        exists = os.path.exists(filename)
        self.file = gio.File(filename)
        if not exists:
            self.file.replace_contents(self.message.encode(coding), None, False)

        if mimetype == "application/octet-stream":
            self.mimetype = self.file.query_info("*").get_content_type()
        else:
            self.mimetype = mimetype

        self.app = gio.app_info_get_default_for_type(self.mimetype, False)
        if self.app:
            self.icon_name = self.app.get_icon().get_names()[0]
        else:
            self.icon_name = None

    def open(self):
        self.app.launch((self.file, ))
