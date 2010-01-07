#!/usr/bin/env python

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
import glib
import os
import pynotify

import mailanie
import preferences
import about
import mail
import maildir
import addressbook

import cairo

_icons = {
    "mail": ("emblem-mail", _("Mail")),
    "mail-forward": ("mail-forward", _("_Forward Mail")),
    "mail-reply": ("mail-reply-sender", _("_Reply Mail")),
    "mail-reply-all": ("mail-reply-all", _("Reply Mail to _All")),
    "mail-send": ("mail-send", _("_Send Mail")),
    "mail-new": ("mail-message-new", _("_New Mail")),
    "mail-send-receive":("mail-send-receive", _("_Refresh")),
    "folder": ("folder", _("Folder")),
    "inbox": ("emblem-mail", _("Inbox")),
    "read": ("mail-read", _("Read Mail")),
    "unread": ("mail-unread", _("Unread Mail")),
    "sent": ("mail-send", _("Sent Mail")),
    "replied": ("mail-reply-sender", _("Replied Mail")),
    "forwarded": ("mail-forward", _("Forwarded Mail")),
    "junk": ("mail-mark-junk", _("Junk")),
    "draft": ("text-x-generic", _("Draft")),
    "trash": ("user-trash", _("Trash")),
    "delete": ("edit-delete", _("Delete")),
    "address-book": ("x-office-address-book", _("Address Book")),
    "search": ("system-search", _("Search")),
    "clear": ("edit-clear", _("Clear")),
}

_updating_mailboxes = False

class MainWindow(gtk.Window):
    _menu = """
    <ui>
     <toolbar name='Toolbar'>
       <toolitem action='New Mail'/>
       <toolitem action='Refresh'/>
       <toolitem action='Delete'/>
       <toolitem action='Address Book'/>
       <toolitem action='Preferences'/>
       <toolitem action='About'/>
     </toolbar>
    </ui>
    """

    def __init__(self):
        super(MainWindow, self).__init__()

        pynotify.init("Mailanie")
        self.set_title("Mailanie")

        self.pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
            os.path.join(os.path.dirname(__file__), "mailanie.svg"), 600, 600)
        self.connect_after("expose-event", self._expose)

        icon_theme = gtk.icon_theme_get_default()
        icon_factory = gtk.IconFactory()
        icon_factory.add_default()

        for icon in _icons:
            pixbuf = icon_theme.load_icon(_icons[icon][0], 128, 0)
            gtk.icon_theme_add_builtin_icon(icon, 128, pixbuf)
            gtk.stock_add([(icon, _icons[icon][1], 0, 0, None)])
            icon_factory.add(icon, gtk.IconSet(pixbuf))

        self.action_group = gtk.ActionGroup("actions")
        self.action_group.add_actions([
                ("New Mail", "mail-new",
                 None, None, _("Write a New Mail"),
                 lambda action: self.add_writemail_tab()),
                ("Refresh", "mail-send-receive",
                 None, None, _("Refresh the Mail Boxes"),
                 lambda action: self._update_mailbox()),
                ("Delete", "delete",
                 None, None, _("Delete Trash Mails"),
                 lambda action: self._delete_trash_mails()),
                ("Address Book", "address-book",
                 None, None, _("Open Address Book"),
                 lambda action: self._add_tab(mailanie.address_book)),
                ("Preferences", gtk.STOCK_PREFERENCES,
                 None, None, _("Choose Preferences"),
                 lambda action: self.preferences.show_all()),
                ("About", gtk.STOCK_ABOUT,
                 None, None, _("About Mailanie"),
                 lambda action: about.About()),
                ("Quit", gtk.STOCK_QUIT,
                 None, None, _("Quit Mailanie"),
                 lambda action: self.quit()),
                ])

        self.ui_manager = gtk.UIManager()
        self.ui_manager.add_ui_from_string(self._menu)
        self.ui_manager.insert_action_group(self.action_group)

        self.accel_group = self.ui_manager.get_accel_group()
        self.add_accel_group(self.accel_group)

        main_box = gtk.VBox()
        self.add(main_box)

        toolbar_box = gtk.HBox()
        main_box.pack_start(toolbar_box, expand=False)
        toolbar_box.pack_start(self.ui_manager.get_widget("/Toolbar"))

        toolbar = gtk.Toolbar()
        toolbar_box.pack_start(toolbar, expand=False)
        entry = gtk.Entry()
        entry.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, "search")
        entry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, "clear")
        entry.connect("icon-release", self._search_icon)
        entry.connect("activate", lambda entry: self._search_icon(
                entry, gtk.ENTRY_ICON_PRIMARY, None))
        toolbar.add(entry)

        self.paned = gtk.HPaned()
        main_box.pack_start(self.paned)

        self._load_mailbox()
        self._load_address_book()

        self.preferences = preferences.Preferences()
        self.preferences.connect_after("response", self._preference_response)

        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.paned.add2(self.notebook)

        self.connect("destroy", lambda widget: self.quit())

        glib.timeout_add(60000, self._update_mailbox)

        gtk.window_set_default_icon_from_file(
            os.path.join(os.path.dirname(__file__), "mailanie.svg"))

        gtk.rc_parse_string ("""
            style "close-button-style"
            {
              GtkWidget::focus-padding = 0
              GtkWidget::focus-line-width = 0
              xthickness = 0
              ythickness = 0
            }
            widget "*.close-button" style "close-button-style"
            """)

    def _expose(self, widget, event):
        cr = widget.window.cairo_create()

        x, y = self.get_size()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_pixbuf(self.pixbuf, x-450, y-450)
        cr.paint_with_alpha(.15)

        self.set_reallocate_redraws(True)

    def _add_tab(self, page, connections=[]):
        new_tab = not(page.widget in self.notebook.get_children())

        if new_tab:
            new_tab = True
            label = gtk.HBox()
            label.set_spacing(2)
            label.pack_start(page.pretty_label)

            button = gtk.Button()
            button.set_relief(gtk.RELIEF_NONE)
            button.set_name("close-button")
            button.add(
                gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU))
            label.pack_start(button, False, False)

            label.show_all()

            button.connect("clicked", lambda button: self.remove_tab(page))

            page.widget.show_all()
            self.notebook.append_page(page.widget, label)
            self.notebook.set_tab_reorderable(page.widget, True)

        page.connections = connections
        for connection in connections:
            connection.connect()

        page_number = self.notebook.page_num(page.widget)
        self.notebook.set_current_page(page_number)

        return new_tab

    def _send_mail(self, mail):
        self.notebook.remove_page(self.notebook.page_num(mail.widget))
        mail.send()

    def _load_mailbox(self):
        mailanie.mailbox = maildir.MailBox()
        self.paned.add1(mailanie.mailbox.widget)
        mailanie.mailbox.tree_view.connect("row-activated", self.add_folder_tab)
        mailanie.mailbox.widget.show_all()

    def _load_address_book(self):
        mailanie.address_book = addressbook.AddressBook()

    def reload(self):
        self.paned.remove(mailanie.mailbox.widget)
        if mailanie.address_book.widget in self.notebook.get_children():
            self.notebook.remove(mailanie.address_book.widget)
        self._load_mailbox()
        self._load_address_book()

    def add_folder_tab(self, tree_view, path, view_column):
        folder = tree_view.get_model()[path][0]
        folder.list_view.connect("row-activated", self._row_activated, folder)
        if self._add_tab(folder):
            folder.load()
            folder.update()

    def _row_activated(self, list_view, path, view_column, folder):
        header = list_view.get_model()[path][0]
        mail = header.get_mail(folder.mailbox)
        self.add_readmail_tab(header, mail, folder)

    def add_readmail_tab(self, header, readmail, folder):
        header.add_flag("S")
        folder.update_info(header.get_key(), header.get_info())
        readmail.load()

        connections = [
            Connection(readmail.reply_button, "clicked",
                       lambda button: self.add_writemail_tab({
                        "To": readmail["From"],
                        "Subject": "Re: " + (readmail["Subject"] or "")})),
            Connection(readmail.reply_all_button, "clicked",
                       lambda button: self.add_writemail_tab({
                        "To": readmail["From"],
                        "Cc": readmail["Cc"],
                        "Subject": "Re: " + (readmail["Subject"] or "")})),
            Connection(readmail.forward_button, "clicked",
                       lambda button: self.add_writemail_tab({
                        "Subject": "Fw: " + (readmail["Subject"] or "")}))]

        self._add_tab(readmail, connections)

    def add_writemail_tab(self, headers={}):
        writemail = mail.WriteMail()
        for header, value in headers.items():
            writemail[header] = value
        writemail.load()

        connections = [
            Connection(writemail.send_button, "clicked",
                       lambda button: self._send_mail(writemail))]

        self._add_tab(writemail, connections)

    def remove_tab(self, page):
        for connection in page.connections:
            connection.disconnect()
            
        self.notebook.get_tab_label(page.widget).remove(page.pretty_label)
        self.notebook.remove(page.widget)

    def _update_mailbox(self):
        global _updating_mailboxes
        if not _updating_mailboxes:
            _updating_mailboxes = True
            for box in mailanie.mailbox.list_boxes():
                new_mails = box.update()
                if new_mails:
                    title = ngettext("%i new mail in %s", "%i new mails in %s",
                                     len(new_mails)) % (len(new_mails), box.label)
                    text = u"\n\n".join(
                        u"%s\n(%s)" % (new_mail.get_header("Subject"),
                                       ", ".join([header[0] or header[1] for header
                                                  in new_mail.get_header("Address")]))
                        for new_mail in new_mails)
                    title = title.replace("&", "&amp;").replace("<", "&lt;")
                    text = text.replace("&", "&amp;").replace("<", "&lt;")
                    pynotify.Notification(title, text, "emblem-mail").show()
            else:
                _updating_mailboxes = False
                return True

    def _delete_trash_mails(self):
        for box in mailanie.mailbox.list_boxes():
            box.delete_trash_mails()

    def _preference_response(self, dialog, response):
        if response in (gtk.RESPONSE_ACCEPT, gtk.RESPONSE_APPLY):
            self.reload()

        if response in (gtk.RESPONSE_ACCEPT, gtk.RESPONSE_CANCEL):
            self.preferences.hide()

    def _search_icon(self, entry, position, event):
        if position == gtk.ENTRY_ICON_SECONDARY:
            entry.set_text("")

        pagenb = self.notebook.get_current_page()
        if pagenb != -1:
            page = self.notebook.get_nth_page(pagenb)
            page.filter(entry.get_text())

    def quit(self):
        for box in mailanie.mailbox.list_boxes():
            box.unload()
        gtk.main_quit()



class Connection(object):
    def __init__(self, widget, signal, callback):
        self._widget = widget
        self._signal = signal
        self._callback = callback

    def connect(self):
        self._id = self._widget.connect(self._signal, self._callback)

    def disconnect(self):
        self._widget.disconnect(self._id)
