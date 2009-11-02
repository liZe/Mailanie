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

import pickle
import os

import config
import mail

class Folder(object):
    def __init__(self, mailbox, label):
        self.mailbox = mailbox if label == "inbox" else mailbox.get_folder(label)
        self._address = "To" if label == "sent" else "From"
        self.label = label
        self.path = label

        self._headers = []
        self._loaded = False
        self._updating = False

    def load(self, cache_path=None):
        if self._loaded:
            return

        if cache_path:
            self._filename = cache_path
        else:
            name = str(abs(hash(self.mailbox._path)))
            self._filename = os.path.join(config.get("path", "folder"), name)

        try:
            with open(self._filename, "r") as fd:
                self._headers = pickle.load(fd)
        except IOError:
            self._headers = []

        self._loaded = True

    def update(self):
        if self._updating or not self._loaded:
            return

        # TODO: manage flags updates
        mailbox_keys = set(self.mailbox.iterkeys())
        headers_keys = set(header.get_key() for header in self._headers)

        old_keys = headers_keys - mailbox_keys
        self._headers = [new_mail for new_mail in self._headers
                         if new_mail.get_key() not in old_keys]

        new_keys = mailbox_keys - headers_keys

        for header in self._headers:
            header.set_flags(self.mailbox.get_key_flags(header.get_key()))

        for i, key in enumerate(new_keys):
            self._headers.append(
                self.mailbox.get_key_headers(key, self._address))
            yield float(i) / len(new_keys)

        yield 1
        yield old_keys, new_keys

    def delete_trash_mails(self):
        if not self._loaded:
            return

        deleted_mails = [mail for mail in self._headers if "T" in mail.get_flags()]

        for i, mail in enumerate(deleted_mails):
            self._headers.remove(mail)
            self.mailbox.remove(mail.get_key())
            yield float(i) / len(deleted_mails)
        
        yield 1
        yield [mail.get_key() for mail in deleted_mails]

    def unload(self):
        if not self._loaded:
            return

        with open(self._filename, "w") as fd:
            for header in self._headers:
                header.clean()
            pickle.dump(self._headers, fd)

    def update_info(self, key, info):
        old_subpath = self.mailbox._toc[key]
        subdir = os.path.dirname(old_subpath)
        suffix = self.mailbox.colon + info
        new_subpath = os.path.join("cur", key + suffix)
        self.mailbox._toc[key] = new_subpath
        new_path = os.path.join(self.mailbox._path, new_subpath)
        os.rename(os.path.join(self.mailbox._path, old_subpath),
                  os.path.join(self.mailbox._path, new_subpath))
