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

import mailanie

class Preferences(gtk.Dialog):
    def __init__(self):
        super(Preferences, self).__init__(
            _("Mailanie Preferences"),
            buttons=(gtk.STOCK_APPLY, gtk.RESPONSE_APPLY,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.set_has_separator(False)
        self.connect("response", self._response)
        self.options = []
        self.notebook = gtk.Notebook()
        self.vbox.add(self.notebook)

        vbox = VBox()
        self.notebook.append_page(vbox, gtk.Label(_("Folders")))

        frame = vbox.add(_("Mail"))
        frame.add(
            FileChooserBox(
                _("Mailbox"), ("path", "mailbox"), self.options))
        
        frame = vbox.add(_("Address Book"))
        frame.add(
            FileChooserBox(
                _("Address book"), ("path", "addressbook"), self.options))
        
        frame = vbox.add(_("Cache"))
        frame.add(
            FileChooserBox(
                _("Folders"), ("path", "folder"), self.options))
        frame.add(
            FileChooserBox(
                _("Attached files"), ("path", "part"), self.options))

        vbox = VBox()
        self.notebook.append_page(vbox, gtk.Label(_("Mailboxes")))

        # TODO: update combo_list when maildir is updated
        combo_list = [(_("None"), "none")]
        combo_list.extend((box.label, box.path) for box
                          in mailanie.mailbox.list_boxes())
        frame = vbox.add(_("Default Mailboxes"))
        frame.add(
            ComboTextBox(
                _("Draft"), combo_list, ("mailbox", "draft"), self.options))
        frame.add(
            ComboTextBox(
                _("Sent Mail"), combo_list, ("mailbox", "sent"), self.options))
    
        vbox = VBox()
        self.notebook.append_page(vbox, gtk.Label(_("SMTP Server")))

        # TODO: update combo_list when maildir is updated
        frame = vbox.add(_("Server"))
        frame.add(
            EntryBox(
                _("Server"), ("smtp", "server"), self.options))
        frame.add(
            EntryBox(
                _("Port"), ("smtp", "port"), self.options))
        frame.add(
            CheckBox(
                _("Use SSL"), ("smtp", "ssl"), self.options))

        frame = vbox.add(_("User"))
        frame.add(
            EntryBox(
                _("Login"), ("smtp", "login"), self.options))
        frame.add(
            EntryBox(
                _("Password"), ("smtp", "password"), self.options, password=True))
        frame.add(
            EntryBox(
                _("Sender Name"), ("smtp", "name"), self.options))
        frame.add(
            EntryBox(
                _("Sender Address"), ("smtp", "address"), self.options))
    
        self._set_config_options()
        
    def _set_config_options(self):
        for option in self.options:
            try:
                option.set_value(option.type(option.path[0], option.path[1]))
            except ValueError:
                pass

    def _response(self, dialog, response):
        if response in (gtk.RESPONSE_ACCEPT, gtk.RESPONSE_APPLY):
            for option in self.options: 
                mailanie.config.set(option.path[0], option.path[1], str(option.get_value()))
            mailanie.config.write()
        else:
            self._set_config_options()



class VBox(gtk.VBox):
    def __init__(self):
        super(VBox, self).__init__()

    def add(self, title):
        frame = Frame(title)
        self.pack_start(frame, expand=False, fill=False)
        return frame



class Frame(gtk.Frame):
    def __init__(self, title):
        super(Frame, self).__init__()
        self.set_border_width(5)
        self.set_shadow_type(gtk.SHADOW_NONE)
        self.set_label("<b>%s</b>" % title)
        self.get_label_widget().set_use_markup(True)
        self.vbox = gtk.VBox()
        gtk.Frame.add(self, self.vbox)

    def add(self, child):
        self.vbox.add(child)



class ComboTextBox(gtk.HBox):
    def __init__(self, title, combo_list, path, options):
        super(ComboTextBox, self).__init__()
        self.set_border_width(5)
        self.set_spacing(10)
        self.label = gtk.Label(title)
        self.label.set_alignment(0, 0.5)
        self.pack_start(self.label, expand=True, fill=True)
        self.combo = gtk.combo_box_new_text()
        for action in combo_list:
            self.combo.append_text(action[0])
        self.pack_end(self.combo, expand=False)
        self.path = path
        self.get_value = lambda: combo_list[self.combo.get_active()][1]
        self.set_value = lambda x: self.combo.set_active(
            [action[1] for action in combo_list].index(x))
        self.type = mailanie.config.get
        options.append(self)



class FileChooserBox(gtk.HBox):
    def __init__(self, title, path, options):
        super(FileChooserBox, self).__init__()
        self.set_border_width(5)
        self.set_spacing(10)
        self.label = gtk.Label(title)
        self.label.set_alignment(0, 0.5)
        self.pack_start(self.label, expand=True, fill=True)
        self.button = gtk.FileChooserButton(_("Select Your Folder"))
        self.button.set_local_only(False)
        self.button.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.pack_end(self.button, expand=False)
        self.path = path
        self.get_value = self.button.get_uri
        self.set_value = self.button.select_uri
        self.type = mailanie.config.get
        options.append(self)



class CheckBox(gtk.CheckButton):
    def __init__(self, title, path, options):
        super(CheckBox, self).__init__(title)
        self.set_border_width(5)
        self.path = path
        self.get_value = self.get_active
        self.set_value = self.set_active
        self.type = mailanie.config.getboolean
        options.append(self)



class EntryBox(gtk.HBox):
    def __init__(self, title, path, options, password=False):
        super(EntryBox, self).__init__()
        self.set_border_width(5)
        self.set_spacing(10)
        self.label = gtk.Label(title)
        self.label.set_alignment(0, 0.5)
        self.pack_start(self.label, expand=True, fill=True)
        self.entry = gtk.Entry()
        self.entry.set_visibility(not password)
        self.pack_end(self.entry, expand=False)
        self.path = path
        self.get_value = self.entry.get_text
        self.set_value = self.entry.set_text
        self.type = mailanie.config.get
        options.append(self)
